const express = require('express');
const axios = require('axios');
const { ClientCredentials, AuthorizationCode } = require('simple-oauth2');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Onshape OAuth configuration
const config = {
    client: {
        id: process.env.ONSHAPE_CLIENT_ID,
        secret: process.env.ONSHAPE_CLIENT_SECRET
    },
    auth: {
        tokenHost: 'https://oauth.onshape.com',
        tokenPath: '/oauth/token',
        authorizePath: '/oauth/authorize'
    }
};

const client = new AuthorizationCode(config);
const REDIRECT_URI = process.env.ONSHAPE_REDIRECT_URI || `http://localhost:${PORT}/oauth/callback`;
const ONSHAPE_API_BASE = 'https://cad.onshape.com';

// In-memory storage for demo (use database in production)
let userTokens = {};

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Route to initiate OAuth flow
app.get('/oauth/login', (req, res) => {
    const authorizationUri = client.authorizeURL({
        redirect_uri: REDIRECT_URI,
        scope: 'OAuth2ReadPII', // Adjust scopes as needed
        state: 'some-random-state' // In production, generate random state per user
    });

    console.log('Redirecting to Onshape OAuth:', authorizationUri);
    res.redirect(authorizationUri);
});

// OAuth callback route
app.get('/oauth/callback', async (req, res) => {
    const { code, error } = req.query;

    if (error) {
        console.error('OAuth error:', error);
        return res.status(400).json({ error: 'OAuth authorization failed', details: error });
    }

    if (!code) {
        return res.status(400).json({ error: 'No authorization code received' });
    }

    try {
        // Exchange authorization code for access token
        const tokenParams = {
            code,
            redirect_uri: REDIRECT_URI,
            scope: 'OAuth2ReadPII'
        };

        const accessToken = await client.getToken(tokenParams);
        const userId = 'user_' + Date.now(); // Generate or get actual user ID

        // Store the token object (it includes refresh functionality)
        userTokens[userId] = accessToken;

        console.log('OAuth successful for user:', userId);
        console.log('Token expires at:', accessToken.token.expires_at);

        res.json({
            success: true,
            message: 'OAuth authentication successful',
            userId: userId,
            expiresAt: accessToken.token.expires_at
        });

    } catch (error) {
        console.error('Token exchange error:', error.message);
        res.status(500).json({
            error: 'Failed to exchange authorization code for tokens',
            details: error.message
        });
    }
});

// Middleware to ensure valid access token
async function getValidToken(userId) {
    let tokenObject = userTokens[userId];

    if (!tokenObject) {
        throw new Error('No access token found for user');
    }

    // Check if token is expired and refresh if needed
    if (tokenObject.expired()) {
        console.log('Token expired, refreshing...');
        try {
            tokenObject = await tokenObject.refresh();
            userTokens[userId] = tokenObject; // Update stored token
            console.log('Token refreshed successfully');
        } catch (error) {
            console.error('Token refresh failed:', error.message);
            throw new Error('Failed to refresh token');
        }
    }

    return tokenObject.token.access_token;
}

// Generic function to make authenticated Onshape API calls
async function callOnshapeAPI(userId, endpoint, params = {}) {
    try {
        const accessToken = await getValidToken(userId);

        const response = await axios.get(`${ONSHAPE_API_BASE}/api/${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            params
        });

        return response.data;
    } catch (error) {
        if (error.response?.status === 401) {
            throw new Error('Authentication failed - token may be invalid');
        }
        throw error;
    }
}

// Example API route to fetch user info from Onshape
app.get('/api/user/:userId', async (req, res) => {
    const { userId } = req.params;

    try {
        const userData = await callOnshapeAPI(userId, 'users/sessioninfo');
        res.json(userData);
    } catch (error) {
        console.error('User API error:', error.message);
        res.status(error.response?.status || 500).json({
            error: 'Failed to fetch user info',
            details: error.message
        });
    }
});

// Example API route to list documents
app.get('/api/documents/:userId', async (req, res) => {
    const { userId } = req.params;

    try {
        const documents = await callOnshapeAPI(userId, 'documents', req.query);
        res.json(documents);
    } catch (error) {
        console.error('Documents API error:', error.message);
        res.status(error.response?.status || 500).json({
            error: 'Failed to fetch documents',
            details: error.message
        });
    }
});

// Generic Onshape API proxy route - fallback approach
app.use('/api/onshape/:userId', async (req, res) => {
    const { userId } = req.params;
    const apiPath = req.path.replace(`/api/onshape/${userId}/`, '');

    if (!apiPath || apiPath === req.path) {
        return res.status(400).json({ error: 'API path is required' });
    }

    try {
        const data = await callOnshapeAPI(userId, apiPath, req.query);
        res.json(data);
    } catch (error) {
        console.error('Onshape API error:', error.message);
        res.status(error.response?.status || 500).json({
            error: 'Onshape API call failed',
            details: error.message
        });
    }
});

// Route to check token status
app.get('/api/token-status/:userId', (req, res) => {
    const { userId } = req.params;
    const tokenObject = userTokens[userId];

    if (!tokenObject) {
        return res.status(404).json({ error: 'No token found for user' });
    }

    res.json({
        expired: tokenObject.expired(),
        expiresAt: tokenObject.token.expires_at,
        hasRefreshToken: !!tokenObject.token.refresh_token
    });
});

// Route to manually refresh token
app.post('/api/refresh-token/:userId', async (req, res) => {
    const { userId } = req.params;
    let tokenObject = userTokens[userId];

    if (!tokenObject) {
        return res.status(404).json({ error: 'No token found for user' });
    }

    try {
        tokenObject = await tokenObject.refresh();
        userTokens[userId] = tokenObject;

        res.json({
            success: true,
            message: 'Token refreshed successfully',
            expiresAt: tokenObject.token.expires_at
        });
    } catch (error) {
        console.error('Manual token refresh error:', error.message);
        res.status(500).json({
            error: 'Failed to refresh token',
            details: error.message
        });
    }
});

// Health check route
app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        activeUsers: Object.keys(userTokens).length
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Onshape OAuth server running on port ${PORT}`);
    console.log(`OAuth login URL: http://localhost:${PORT}/oauth/login`);
    console.log('\nRequired environment variables:');
    console.log('- ONSHAPE_CLIENT_ID');
    console.log('- ONSHAPE_CLIENT_SECRET');
    console.log('- ONSHAPE_REDIRECT_URI (optional)');
    console.log('\nInstall dependencies: npm install express axios simple-oauth2 dotenv');
});

module.exports = app;