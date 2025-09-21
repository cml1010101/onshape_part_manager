const path = require('path');
const uuid = require('uuid');

const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');

const passport = require('passport');
const OnshapeStrategy = require('passport-onshape');

require('dotenv').config();

config = {
    oauthClientId: process.env.ONSHAPE_CLIENT_ID,
    oauthClientSecret: process.env.ONSHAPE_CLIENT_SECRET,
    oauthCallbackUrl: process.env.OAUTH_CALLBACK_URL,
    oauthUrl: process.env.OAUTH_URL || 'https://oauth.onshape.com',
    sessionSecret: process.env.SESSION_SECRET
}

const app = express();

app.use(bodyParser.json());

app.set('trust proxy', 1); // To allow to run correctly behind Heroku when deployed

app.use(session({
    secret: config.sessionSecret,
    saveUninitialized: false,
    resave: false,
    cookie: {
        name: 'onshape-webhook-app',
        sameSite: 'none',
        secure: true,
        httpOnly: true,
        path: '/',
        maxAge: 1000 * 60 * 60 * 24 // 1 day
    }
}));
app.use(passport.initialize());
app.use(passport.session());

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

passport.use(new OnshapeStrategy({
        clientID: config.oauthClientId,
        clientSecret: config.oauthClientSecret,
        callbackURL: config.oauthCallbackUrl,
        authorizationURL: `${config.oauthUrl}/oauth/authorize`,
        tokenURL: `${config.oauthUrl}/oauth/token`,
        userProfileURL: `${config.oauthUrl}/api/users/sessioninfo`
    },
    (accessToken, refreshToken, profile, done) => {
        profile.accessToken = accessToken;
        profile.refreshToken = refreshToken;
        return done(null, profile);
    }
));

app.use('/oauthSignin', (req, res) => {
    /* These 5 lines are specific to the glTF Viewer sample app. You can replace them with the input for whatever Onshape endpoints you are using in your app */
    const state = {
        docId: req.query.documentId,
        workId: req.query.workspaceId,
        elId: req.query.elementId
    };
    req.session.state = state;
    return passport.authenticate('onshape', { state: uuid.v4(state) })(req, res);
}, (req, res) => {    

});

app.use('/oauthRedirect', passport.authenticate('onshape', { failureRedirect: '/grantDenied' }), (req, res) => {
    /* This code is specific to the glTF Viewer sample app. You can replace it with the input for whatever Onshape endpoints you are using in your app. */
    res.redirect(`/?documentId=${req.session.state.docId}
&workspaceId=${req.session.state.workId}&elementId=
    ${req.session.state.elId}`);
});

app.get('/grantDenied', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'html', 'grantDenied.html'));
})

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
                return res.sendFile(path.join(__dirname, 'public', 'html', 'index.html'));
            });
        }).catch(() => {
            // Refresh token failed, take the user to OAuth sign in page.
            return res.redirect(`/oauthSignin${req._parsedUrl.search ? req._parsedUrl.search : ""}`);
        });
    }
});

//Refresh the access token
const refreshAccessToken = async (user) => {
    const body = 'grant_type=refresh_token&refresh_token=' + user.refreshToken + '&client_id=' + config.oauthClientId + '&client_secret=' + config.oauthClientSecret;
    let res = await fetch(config.oauthUrl + "/oauth/token", {
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

module.exports = app;
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});