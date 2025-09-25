const path = require('path');
const uuid = require('uuid');
const crypto = require('crypto');

const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');

const passport = require('passport');
const OnshapeStrategy = require('passport-onshape');

const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.set('trust proxy', 1); // To allow to run correctly behind Heroku when deployed

const SESSION_SECRET = process.env.SESSION_SECRET;
const OAUTH_CLIENT_ID = process.env.OAUTH_CLIENT_ID;
const OAUTH_CLIENT_SECRET = process.env.OAUTH_CLIENT_SECRET;
const OAUTH_CALLBACK_URL = process.env.OAUTH_CALLBACK_URL;
const OAUTH_URL = process.env.OAUTH_URL || 'https://oauth.onshape.com';
const PORT = process.env.PORT || 3000;

// OAuth Provider configuration (for when Onshape accesses your app)
const PROVIDER_CLIENT_ID = process.env.PROVIDER_CLIENT_ID || 'your-app-client-id';
const PROVIDER_CLIENT_SECRET = process.env.PROVIDER_CLIENT_SECRET || 'your-app-client-secret';

// In-memory stores (use database in production)
const authorizationCodes = new Map(); // code -> { userId, clientId, redirectUri, expiresAt, scopes }
const accessTokens = new Map(); // token -> { userId, clientId, scopes, expiresAt }
const refreshTokens = new Map(); // refreshToken -> { userId, clientId, scopes }
const clients = new Map([
    // Register Onshape as a client (you'd configure this in Onshape's developer settings)
    ['onshape-client-id', {
        clientId: PROVIDER_CLIENT_ID,
        clientSecret: PROVIDER_CLIENT_SECRET,
        redirectUris: ['https://cad.onshape.com/oauth/callback'] // Example redirect URI
    }]
]);

console.log(`Using Onshape OAuth URL: ${OAUTH_URL}`);
console.log(`PROVIDER Client ID: ${PROVIDER_CLIENT_ID}`);
console.log(`PROVIDER Client Secret: ${PROVIDER_CLIENT_SECRET}`);

app.use(session({
    secret: SESSION_SECRET,
    saveUninitialized: false,
    resave: false,
    cookie: {
        name: 'app-testapp-session',
        sameSite: 'none',
        secure: true,
        httpOnly: true,
        path: '/',
        maxAge: 1000 * 60 * 60 * 24 // 1 day
    }
}));
app.use(passport.initialize());
app.use(passport.session());

// Existing Onshape OAuth consumer setup
passport.use(new OnshapeStrategy({
        clientID: OAUTH_CLIENT_ID,
        clientSecret: OAUTH_CLIENT_SECRET,
        callbackURL: OAUTH_CALLBACK_URL,
        authorizationURL: `${OAUTH_URL}/oauth/authorize`,
        tokenURL: `${OAUTH_URL}/oauth/token`,
        userProfileURL: `${OAUTH_URL}/api/users/sessioninfo`
    },
    (accessToken, refreshToken, profile, done) => {
        profile.accessToken = accessToken;
        profile.refreshToken = refreshToken;
        return done(null, profile);
    }
));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

// Existing OAuth consumer routes
app.use('/oauthSignin', (req, res) => {
    return passport.authenticate('onshape', { state: uuid.v4() })(req, res);
}, (req, res) => { /* redirected to Onshape for authentication */ });

app.use('/oauthRedirect', passport.authenticate('onshape', { failureRedirect: '/grantDenied' }), (req, res) => {
    res.redirect(`/`);
});

app.get('/grantDenied', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'html', 'grantDenied.html'));
});

app.get('/', (req, res) => {
    if (!req.user) {
        return res.redirect(`/oauthSignin${req._parsedUrl.search ? req._parsedUrl.search : ""}`);
    } else {
        refreshAccessToken(req.user).then((tokenJson) => {
            let usrObj = JSON.parse(JSON.stringify(req.user));
            usrObj.accessToken = tokenJson.access_token;
            usrObj.refreshToken = tokenJson.refresh_token;
            req.login(usrObj, () => {
                console.log('Serving index.html to user ' + req.user.id);
                return res.sendFile(path.join(__dirname, 'public', 'html', 'index.html'));
            });
        }).catch(() => {
            return res.redirect(`/oauthSignin${req._parsedUrl.search ? req._parsedUrl.search : ""}`);
        });
    }
});

// ================================
// OAuth PROVIDER endpoints (for Onshape to access your app)
// ================================

// Authorization endpoint - where Onshape redirects users for consent
app.get('/oauth/authorize', (req, res) => {
    const { response_type, client_id, redirect_uri, scope, state } = req.query;
    
    // Validate request
    if (response_type !== 'code') {
        return res.status(400).json({ error: 'unsupported_response_type' });
    }
    
    const client = clients.get(client_id);
    if (!client) {
        console.warn(`Unknown client_id: ${client_id}`);
        return res.status(400).json({ error: 'invalid_client' });
    }
    
    if (!client.redirectUris.includes(redirect_uri)) {
        return res.status(400).json({ error: 'invalid_redirect_uri' });
    }
    
    // Check if user is authenticated with your app
    if (!req.user) {
        // Store the OAuth request and redirect to your app's login
        req.session.pendingOAuth = { response_type, client_id, redirect_uri, scope, state };
        return res.redirect('/oauthSignin');
    }
    
    // Show consent page
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorize Application</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
                .consent-form { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                button { padding: 10px 20px; margin: 10px; cursor: pointer; }
                .approve { background: #4CAF50; color: white; border: none; }
                .deny { background: #f44336; color: white; border: none; }
            </style>
        </head>
        <body>
            <div class="consent-form">
                <h2>Authorize Access</h2>
                <p><strong>${client_id}</strong> wants to access your account.</p>
                <p>Requested permissions: ${scope || 'basic access'}</p>
                <p>This will allow the application to access your data on your behalf.</p>
                
                <form method="POST" action="/oauth/authorize">
                    <input type="hidden" name="client_id" value="${client_id}">
                    <input type="hidden" name="redirect_uri" value="${redirect_uri}">
                    <input type="hidden" name="scope" value="${scope || ''}">
                    <input type="hidden" name="state" value="${state || ''}">
                    <input type="hidden" name="response_type" value="${response_type}">
                    
                    <button type="submit" name="action" value="approve" class="approve">Approve</button>
                    <button type="submit" name="action" value="deny" class="deny">Deny</button>
                </form>
            </div>
        </body>
        </html>
    `);
});

// Handle consent form submission
app.post('/oauth/authorize', (req, res) => {
    const { action, client_id, redirect_uri, scope, state, response_type } = req.body;
    
    if (!req.user) {
        return res.status(401).json({ error: 'unauthorized' });
    }
    
    if (action === 'deny') {
        return res.redirect(`${redirect_uri}?error=access_denied&state=${state || ''}`);
    }
    
    if (action === 'approve') {
        // Generate authorization code
        const code = crypto.randomBytes(32).toString('hex');
        const expiresAt = Date.now() + (10 * 60 * 1000); // 10 minutes
        
        authorizationCodes.set(code, {
            userId: req.user.id,
            clientId: client_id,
            redirectUri: redirect_uri,
            scopes: scope ? scope.split(' ') : [],
            expiresAt
        });
        
        // Redirect back to client with code
        const redirectUrl = new URL(redirect_uri);
        redirectUrl.searchParams.set('code', code);
        if (state) redirectUrl.searchParams.set('state', state);
        
        return res.redirect(redirectUrl.toString());
    }
    
    return res.status(400).json({ error: 'invalid_request' });
});

// Token endpoint - where Onshape exchanges code for access token
app.post('/oauth/token', (req, res) => {
    const { grant_type, code, redirect_uri, client_id, client_secret, refresh_token } = req.body;
    
    // Validate client credentials
    const client = clients.get(client_id);
    if (!client || client.clientSecret !== client_secret) {
        return res.status(401).json({ error: 'invalid_client' });
    }
    
    if (grant_type === 'authorization_code') {
        // Exchange authorization code for access token
        const authCode = authorizationCodes.get(code);
        if (!authCode) {
            return res.status(400).json({ error: 'invalid_grant' });
        }
        
        if (Date.now() > authCode.expiresAt) {
            authorizationCodes.delete(code);
            return res.status(400).json({ error: 'invalid_grant' });
        }
        
        if (authCode.clientId !== client_id || authCode.redirectUri !== redirect_uri) {
            return res.status(400).json({ error: 'invalid_grant' });
        }
        
        // Generate tokens
        const accessToken = crypto.randomBytes(32).toString('hex');
        const newRefreshToken = crypto.randomBytes(32).toString('hex');
        const expiresIn = 3600; // 1 hour
        
        accessTokens.set(accessToken, {
            userId: authCode.userId,
            clientId: client_id,
            scopes: authCode.scopes,
            expiresAt: Date.now() + (expiresIn * 1000)
        });
        
        refreshTokens.set(newRefreshToken, {
            userId: authCode.userId,
            clientId: client_id,
            scopes: authCode.scopes
        });
        
        // Clean up authorization code
        authorizationCodes.delete(code);
        
        return res.json({
            access_token: accessToken,
            refresh_token: newRefreshToken,
            token_type: 'Bearer',
            expires_in: expiresIn,
            scope: authCode.scopes.join(' ')
        });
        
    } else if (grant_type === 'refresh_token') {
        // Handle refresh token
        const refreshTokenData = refreshTokens.get(refresh_token);
        if (!refreshTokenData || refreshTokenData.clientId !== client_id) {
            return res.status(400).json({ error: 'invalid_grant' });
        }
        
        // Generate new access token
        const accessToken = crypto.randomBytes(32).toString('hex');
        const expiresIn = 3600; // 1 hour
        
        accessTokens.set(accessToken, {
            userId: refreshTokenData.userId,
            clientId: client_id,
            scopes: refreshTokenData.scopes,
            expiresAt: Date.now() + (expiresIn * 1000)
        });
        
        return res.json({
            access_token: accessToken,
            token_type: 'Bearer',
            expires_in: expiresIn,
            scope: refreshTokenData.scopes.join(' ')
        });
        
    } else {
        return res.status(400).json({ error: 'unsupported_grant_type' });
    }
});

// Protected API endpoint that Onshape can call with the access token
app.get('/api/user', authenticateToken, (req, res) => {
    // Return user info that Onshape requested
    res.json({
        id: req.tokenData.userId,
        scopes: req.tokenData.scopes,
        message: 'Successfully accessed your webapp API from Onshape!'
    });
});

// Example protected resource endpoint
app.get('/api/data', authenticateToken, (req, res) => {
    res.json({
        userId: req.tokenData.userId,
        data: 'This is protected data from your webapp',
        timestamp: new Date().toISOString(),
        scopes: req.tokenData.scopes
    });
});

// Middleware to authenticate Bearer tokens
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN
    
    if (!token) {
        return res.status(401).json({ error: 'missing_token' });
    }
    
    const tokenData = accessTokens.get(token);
    if (!tokenData) {
        return res.status(401).json({ error: 'invalid_token' });
    }
    
    if (Date.now() > tokenData.expiresAt) {
        accessTokens.delete(token);
        return res.status(401).json({ error: 'token_expired' });
    }
    
    req.tokenData = tokenData;
    next();
}

// Handle pending OAuth after user signs in
app.use((req, res, next) => {
    if (req.user && req.session.pendingOAuth) {
        const pending = req.session.pendingOAuth;
        delete req.session.pendingOAuth;
        
        // Redirect back to authorization endpoint
        const params = new URLSearchParams(pending);
        return res.redirect(`/oauth/authorize?${params}`);
    }
    next();
});

// Existing refresh token function
const refreshAccessToken = async (user) => {
    const body = 'grant_type=refresh_token&refresh_token=' + user.refreshToken + '&client_id=' + OAUTH_CLIENT_ID + '&client_secret=' + OAUTH_CLIENT_SECRET;
    let res = await fetch(OAUTH_URL + "/oauth/token", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: body
    });
    if (res.ok) {
        return await res.json();
    } else {
        throw new Error("Could not refresh access token, please sign in again.");
    }
}

app.listen(PORT, () => {
    console.log(`App listening on port ${PORT}`);
    console.log(`OAuth Authorization URL: https://onshape-part-manager.onrender.com/oauth/authorize`);
    console.log(`OAuth Token URL: https://onshape-part-manager.onrender.com/oauth/token`);
});