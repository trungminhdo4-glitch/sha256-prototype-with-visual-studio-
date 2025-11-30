const crypto = require('crypto');

class block {
    constructor(index, timestamp, data, previousHash = '') {
        this.index = index;
        this.timestamp = timestamp;
        this.data = data;
        this.previousHash = previousHash;
        this.hash = this.calculateHash();
    }

    calculateHash() {
        const input = this.index + this.previousHash + this.timestamp + JSON.stringify(this.data);
        return crypto.createHash('sha256').update(input).digest('hex');
    }
}

class Blockchain {
    constructor() {
        this.chain = [this.createGenesisBlock()];
    }

    createGenesisBlock() {
        return new block(0, "01/01/2024", "Genesis Block", "0");
    }

    getlatestBlock() {
        return this.chain[this.chain.length - 1];
    }

    addblock(newblock) {
        newblock.previousHash = this.getlatestBlock().hash;
        newblock.hash = newblock.calculateHash();
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
mycoin.addblock(new block(1, "02/01/2024", { amount: 4 }));
mycoin.addblock(new block(2, "03/01/2024", { amount: 10 }));

console.log('Is blockchain valid? ' + mycoin.ischainValid());
 console.log(JSON.stringify(mycoin, null, 4));

 mycoin.chain[1].data = { amount: 100 };

 mycoin.chain[1].hash = mycoin.chain[1].calculateHash();
 console.log ('Is blockchain valid? ' + mycoin.ischainValid());
