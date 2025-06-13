const { MongoClient } = require('mongodb');
require('dotenv').config();

const uri = process.env.MONGO_URI;

let db;

async function connectDB() {
  try {
    const client = new MongoClient(uri);
    await client.connect();
    db = client.db(); // domyślnie sample_airbnb
    console.log('✅ Połączono z MongoDB Atlas');
  } catch (err) {
    console.error('❌ Błąd połączenia z MongoDB:', err.message);
  }
}

function getDB() {
  return db;
}

module.exports = connectDB;
module.exports.getDB = getDB;