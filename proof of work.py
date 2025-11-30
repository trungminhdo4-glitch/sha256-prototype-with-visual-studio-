const crypto = require('crypto');

class block {
    constructor(index, timestamp, data, previousHash = '') {
        this.index = index;
        this.timestamp = timestamp;
        this.data = data;
        this.previousHash = previousHash;
        this.nonce = 0;
        this.hash = this.calculateHash();
    }

    calculateHash() {
        const input = this.index + this.previousHash + this.timestamp + JSON.stringify(this.data) + this.nonce;
        return crypto.createHash('sha256').update(input).digest('hex');
    }

    mineBlock(difficulty) {
        while (this.hash.substring(0, difficulty) !== Array(difficulty + 1).join("0")) {
            this.nonce++;
            this.hash = this.calculateHash();
            console.log("Block mined: " + this.hash);
        }
    }
}

class Blockchain {
    constructor() {
        this.chain = [this.createGenesisBlock()];
        this.difficulty = 4;
    }

    createGenesisBlock() {
        return new block(0, "01/01/2024", "Genesis Block", "0");
    }

    getlatestBlock() {
        return this.chain[this.chain.length - 1];
    }

    addblock(newblock) {
        newblock.previousHash = this.getlatestBlock().hash;
        newblock.mineBlock(this.difficulty);
        this.chain.push(newblock);
    }

    ischainValid() {
        for (let i = 1; i < this.chain.length; i++) {
            const currentBlock = this.chain[i];
            const previousBlock = this.chain[i - 1];

            if (currentBlock.hash !== currentBlock.calculateHash()) {
                return false;
            }

            if (currentBlock.previousHash !== previousBlock.hash) {
                return false;
            }
        }
        return true;
    }
}

let mycoin = new Blockchain();

console.log("Mining block 1...");
mycoin.addblock(new block(1, "02/01/2024", { amount: 4 }));
console.log("Mining block 2...");
mycoin.addblock(new block(2, "03/01/2024", { amount: 10 }));

console.log('Is blockchain valid? ' + mycoin.ischainValid());
console.log(JSON.stringify(mycoin, null, 4));
