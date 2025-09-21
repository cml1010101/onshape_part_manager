const path = require('path');
const uuid = require('uuid');

const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');

const passport = require('passport');
const OnshapeStrategy = require('passport-onshape');

const app = express();

app.use(bodyParser.json());

app.set('trust proxy', 1); // To allow to run correctly behind Heroku when deployed

const SESSION_SECRET = process.env.SESSION_SECRET;
const OAUTH_CLIENT_ID = process.env.OAUTH_CLIENT_ID;
const OAUTH_CLIENT_SECRET = process.env.OAUTH_CLIENT_SECRET;
const OAUTH_CALLBACK_URL = process.env.OAUTH_CALLBACK_URL;
const OAUTH_URL = process.env.OAUTH_URL || 'https://oauth.onshape.com';
const PORT = process.env.PORT || 3000;

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

app.use('/oauthSignin', (req, res) => {
    return passport.authenticate('onshape', { state: uuid.v4() })(req, res);
}, (req, res) => { /* redirected to Onshape for authentication */ });

app.use('/oauthRedirect', passport.authenticate('onshape', { failureRedirect: '/grantDenied' }), (req, res) => {
    /* This code is specific to the glTF Viewer sample app. You can replace it with the input for whatever Onshape endpoints you are using in your app. */
    res.redirect(`/`);
});

app.get('/grantDenied', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'html', 'grantDenied.html'));
})

/**
 * After landing on the home page, we check if a user had already signed in.
 * If no user has signed in, we redirect the request to the OAuth sign-in page.
 * If a user had signed in previously, we will attempt to refresh the access token of the user.
 * After successfully refreshing the access token, we will simply take the user to the landing page of the app.
 * If the refresh token request fails, we will redirect the user to the OAuth sign-in page again. 
 */
app.get('/', (req, res) => {
    if (!req.user) {
        return res.redirect(`/oauthSignin${req._parsedUrl.search ? req._parsedUrl.search : ""}`);
    } else {
        refreshAccessToken(req.user).then((tokenJson) => {
            // Dereference the user object and update the access token and refresh token in the in-memory object.
            let usrObj = JSON.parse(JSON.stringify(req.user));
            usrObj.accessToken = tokenJson.access_token;
            usrObj.refreshToken = tokenJson.refresh_token;
            // Update the user object in PassportJS. No redirections will happen here, this is a purely internal operation.
            req.login(usrObj, () => {
                console.log('Serving index.html to user ' + req.user.id);
                return res.sendFile(path.join(__dirname, 'public', 'html', 'index.html'));
            });
        }).catch(() => {
            // Refresh token failed, take the user to OAuth sign in page.
            return res.redirect(`/oauthSignin${req._parsedUrl.search ? req._parsedUrl.search : ""}`);
        });
    }
});

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
});