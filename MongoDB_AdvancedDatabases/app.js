const express = require('express');
const connectDB = require('./db');
const listingsRoutes = require('./routes/listings');
const setupSwagger = require('./docs/swagger');
const path = require('path');

const app = express();
app.use(express.json());

app.use(express.static(path.join(__dirname, 'public')));

connectDB();
setupSwagger(app);
app.use('/api/listings', listingsRoutes);

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log('Swagger docs available at http://localhost:3000/api-docs');
});