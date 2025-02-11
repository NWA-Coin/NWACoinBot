const { Connection, PublicKey, clusterApiUrl } = require('@solana/web3.js');
const { TOKEN_PROGRAM_ID } = require('@solana/spl-token');

// Initialize Solana connection with fallback endpoints and proper config
const RPC_ENDPOINTS = [
    'https://api.mainnet-beta.solana.com',
    'https://solana-api.projectserum.com',
    clusterApiUrl('mainnet-beta')
];

let currentEndpointIndex = 0;
let connection = new Connection(RPC_ENDPOINTS[currentEndpointIndex], {
    commitment: 'confirmed',
    confirmTransactionInitialTimeout: 60000,
    disableRetryOnRateLimit: false
});

async function validateConnection() {
    try {
        const slot = await connection.getSlot();
        console.log(`Successfully connected to ${RPC_ENDPOINTS[currentEndpointIndex]}, current slot: ${slot}`);
        return true;
    } catch (error) {
        console.error(`Connection failed for endpoint ${RPC_ENDPOINTS[currentEndpointIndex]}:`, error.message);
        console.error('Full error:', JSON.stringify(error, null, 2));

        // Try next endpoint
        currentEndpointIndex = (currentEndpointIndex + 1) % RPC_ENDPOINTS.length;
        connection = new Connection(RPC_ENDPOINTS[currentEndpointIndex], {
            commitment: 'confirmed',
            confirmTransactionInitialTimeout: 60000,
            disableRetryOnRateLimit: false
        });
        return false;
    }
}

async function getTokenBalance(walletAddress, mintAddress) {
    try {
        // Validate connection first
        let isValid = await validateConnection();
        let retries = 3;
        while (!isValid && retries > 0) {
            console.log(`Retrying connection validation, attempts left: ${retries}`);
            isValid = await validateConnection();
            retries--;
            if (!isValid && retries > 0) {
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s between retries
            }
        }

        if (!isValid) {
            throw new Error('Failed to establish connection to Solana network after multiple attempts');
        }

        console.log(`Using RPC endpoint: ${RPC_ENDPOINTS[currentEndpointIndex]}`);
        console.log(`Checking balance for wallet: ${walletAddress}`);
        console.log(`Token mint address: ${mintAddress}`);

        // Validate addresses
        let wallet, mint;
        try {
            wallet = new PublicKey(walletAddress);
            mint = new PublicKey(mintAddress);
            console.log('Addresses validated successfully');
        } catch (error) {
            throw new Error(`Invalid address format: ${error.message}`);
        }

        // Get all token accounts for this wallet
        console.log('Fetching token accounts...');
        const tokenAccounts = await connection.getParsedTokenAccountsByOwner(
            wallet,
            {
                programId: TOKEN_PROGRAM_ID,
            },
            'confirmed'
        );

        console.log(`Found ${tokenAccounts.value.length} token accounts`);

        // Look for our specific token
        for (const account of tokenAccounts.value) {
            const tokenMint = account.account.data.parsed.info.mint;

            if (tokenMint === mintAddress) {
                const parsedInfo = account.account.data.parsed.info;
                const amount = parsedInfo.tokenAmount.amount;
                const decimals = parsedInfo.tokenAmount.decimals;

                console.log(`Found matching token account`);
                console.log(`Raw amount: ${amount}`);
                console.log(`Decimals: ${decimals}`);

                const adjustedAmount = parseFloat(amount) / Math.pow(10, decimals);
                console.log(`Adjusted amount: ${adjustedAmount}`);

                return {
                    raw: amount,
                    adjusted: adjustedAmount,
                    decimals: decimals
                };
            }
        }

        // If we didn't find the token, return 0 balance
        console.log('No matching token account found, returning zero balance');
        return {
            raw: "0",
            adjusted: 0,
            decimals: 0
        };

    } catch (error) {
        // Log detailed error info
        console.error('Error in getTokenBalance:', {
            error: error.message,
            stack: error.stack,
            walletAddress,
            mintAddress,
            endpoint: RPC_ENDPOINTS[currentEndpointIndex]
        });

        // Throw a clean error that can be caught by Python
        throw new Error(`Failed to get token balance: ${error.message}`);
    }
}

// Export the function
module.exports = {
    getTokenBalance
};