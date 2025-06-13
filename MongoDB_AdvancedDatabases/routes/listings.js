// routes/listings.js
const express = require('express');
const router = express.Router();
const controller = require('../controllers/listingsController');

// CRUD operations
router.get('/', controller.getAllListings);
router.post('/', controller.createListing);
router.put('/:id', controller.updateListing);
router.delete('/:id', controller.deleteListing);
router.get('/my', controller.getMyListings);

// Filter endpoints
router.get('/price/under/:max', controller.getListingsUnderMaxPrice);
router.get('/filter-by-params', controller.filterListings);

// Embedded reviews
router.get('/:id/reviews', controller.getListingReviews);
router.post('/:id/reviews', controller.addReview);

//Amenities
router.patch('/:id/amenities/add', controller.addAmenity);
router.patch('/:id/amenities/remove', controller.removeAmenity);

// Statistics
router.get('/statistics/avg', controller.getAveragePrice);
router.get('/statistics/count', controller.getListingsCount);
router.get('/statistics/fields-summary', controller.getFieldStats);

// Extra
router.get('/random', controller.getRandomListing);
router.get('/:id', controller.getListingById);


module.exports = router;