// controllers/listingsController.js
const {getDB} = require('../db');
const {ObjectId} = require('mongodb');

const { buildOptionalFields } = require('./utils');

// Get first 10 listings (basic pagination)
exports.getAllListings = async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const pageSize = 10;

        const collection = getDB().collection('listingsAndReviews');

        const totalCount = await collection.estimatedDocumentCount();
        const totalPages = Math.ceil(totalCount / pageSize);

        if (totalPages > 0 && (page < 1 || page > totalPages)) {
            return res.status(400).json({
                error: `Page out of range. Total pages: ${totalPages}`
            });
        }

        const listings = await collection
            .find({})
            .skip((page - 1) * pageSize)
            .limit(pageSize)
            .toArray();

        res.json({
            currentPage: page,
            totalPages,
            totalCount,
            pageSize,
            listings
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Create a new listing with selected fields
exports.createListing = async (req, res) => {
    try {
        const {
            name, price, address, amenities,
            room_type, property_type, host
        } = req.body;

        if (
            !name || typeof name !== 'string' ||
            !price || isNaN(+price) ||
            !address?.market || typeof address.market !== 'string' ||
            !address?.country || typeof address.country !== 'string' ||
            !Array.isArray(amenities) || !amenities.length ||
            !room_type || typeof room_type !== 'string' ||
            !property_type || typeof property_type !== 'string' ||
            !host?.host_name || typeof host.host_name !== 'string' ||
            !Array.isArray(host.host_verifications) || !host.host_verifications.length
        ) {
            return res.status(400).json({
                error: "Missing or invalid required fields: name*, price*, address.market*, address.country*, amenities*, room_type*, property_type*, host.host_name*, host.host_verifications*"
            });
        }

        const listing = {
            _id: `${Date.now()}-${Math.floor(Math.random() * 1000000)}`,
            name,
            price: Number(price),
            address,
            amenities,
            room_type,
            property_type,
            host: {
                ...(req.body.host || {}),
                host_id: "default_host_001"
            },
            ...buildOptionalFields(req.body)
        };

        const result = await getDB().collection('listingsAndReviews').insertOne(listing);
        listing._id = result.insertedId.toString();

        res.status(201).json(listing);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Update listing by ID
exports.updateListing = async (req, res) => {
    try {
        const id = req.params.id;
        const hostId = req.query.host_id; // alias na host.Id

        if (!id || typeof id !== 'string') {
            return res.status(400).json({ error: 'Missing or invalid ID' });
        }

        if (!hostId || typeof hostId !== 'string') {
            return res.status(400).json({ error: 'Host identification (host_id) required.' });
        }

        const {
            name,
            price,
            address,
            amenities,
            room_type,
            property_type,
            host
        } = req.body;

        const updateDoc = {
            ...(name && { name }),
            ...(price && !isNaN(Number(price)) && { price: Number(price) }),
            ...(address && typeof address === 'object' && { address }),
            ...(Array.isArray(amenities) && amenities.length > 0 && { amenities }),
            ...(room_type && { room_type }),
            ...(property_type && { property_type }),
            ...buildOptionalFields(req.body)
        };

        if (host && typeof host === 'object') {
            // Oddzielnie aktualizujemy host bez naruszania host_id
            Object.keys(host).forEach(key => {
                if (key !== 'host_id') {
                    updateDoc[`host.${key}`] = host[key];
                }
            });
        }

        if (Object.keys(updateDoc).length === 0) {
            return res.status(400).json({ error: 'No valid fields provided for update.' });
        }

        const result = await getDB()
            .collection('listingsAndReviews')
            .updateOne(
                { _id: id, "host.host_id": hostId },
                { $set: updateDoc }
            );

        if (result.matchedCount === 0) {
            return res.status(404).json({ error: 'Listing not found or not owned by this host.' });
        }

        res.json({ message: 'Listing updated successfully.' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

exports.getMyListings = async (req, res) => {
    try {
        const hostId = req.query.host_id;
        if (!hostId) {
            return res.status(400).json({ error: "Missing host_id in query." });
        }

        const listings = await getDB()
            .collection('listingsAndReviews')
            .find({ "host.host_id": hostId })
            .toArray();

        res.json(listings);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Delete listing by ID
exports.deleteListing = async (req, res) => {
    try {
        const id = req.params.id;

        if (!id || typeof id !== 'string') {
            return res.status(400).json({ error: 'Missing or invalid ID' });
        }

        const result = await getDB()
            .collection('listingsAndReviews')
            .deleteOne({ _id: id });

        if (result.deletedCount === 0) {
            return res.status(404).json({ error: 'Listing not found.' });
        }

        res.json({ message: 'Listing deleted successfully.' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Get listing by ID
exports.getListingById = async (req, res) => {
    try {
        const { id } = req.params;

        if (!id || typeof id !== 'string') {
            return res.status(400).json({ error: 'Missing or invalid ID' });
        }

        const listing = await getDB()
            .collection('listingsAndReviews')
            .findOne({ _id: id });

        if (!listing) {
            return res.status(404).json({ message: 'Listing not found' });
        }

        res.json(listing);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Listings cheaper than max price
exports.getListingsUnderMaxPrice = async (req, res) => {
    try {
        const maxPrice = parseFloat(req.params.max);
        const page = parseInt(req.query.page) || 1;
        const pageSize = 10;
        const sortOrder = req.query.sort === 'desc' ? -1 : 1; // default: ascending

        const cursor = getDB().collection('listingsAndReviews')
            .find({price: {$lt: maxPrice}})
            .sort({price: sortOrder}) // sort ascending or descending
            .skip((page - 1) * pageSize)
            .limit(pageSize);

        const listings = await cursor.toArray();
        res.json(listings);
    } catch (err) {
        res.status(500).json({error: err.message});
    }
};

// Get embedded reviews (if present)
exports.getListingReviews = async (req, res) => {
    try {
        const { id } = req.params;
        const page = parseInt(req.query.page) || 1;
        const pageSize = 10;

        if (!id || typeof id !== 'string') {
            return res.status(400).json({ error: 'Missing or invalid ID' });
        }

        const collection = getDB().collection('listingsAndReviews');
        const listing = await collection.findOne({ _id: id });

        if (!listing) {
            return res.status(404).json({ error: 'Listing not found' });
        }

        const allReviews = listing.reviews || [];
        const totalReviews = allReviews.length;
        const totalPages = Math.max(1, Math.ceil(totalReviews / pageSize));

        const paginatedReviews = allReviews.slice((page - 1) * pageSize, page * pageSize);

        res.json({
            listingId: id,
            currentPage: page,
            totalPages,
            totalReviews,
            reviews: paginatedReviews
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Add embedded review
exports.addReview = async (req, res) => {
    try {
        const listingId = req.params.id;
        const {_id, reviewer_id, reviewer_name, date, comments} = req.body;

        if (
            !_id || typeof _id !== 'string' ||
            !reviewer_id || typeof reviewer_id !== 'string' ||
            !reviewer_name || typeof reviewer_name !== 'string' ||
            !date || isNaN(Date.parse(date)) ||
            !comments || typeof comments !== 'string'
        ) {
            return res.status(400).json({ error: "Missing or invalid review fields." });
        }

        const review = {
            _id,
            listing_id: listingId,
            reviewer_id,
            reviewer_name,
            date: new Date(date),
            comments
        };

        const result = await getDB().collection('listingsAndReviews')
            .updateOne(
                { _id: listingId },
                {
                    $push: {
                        reviews: {
                            $each: [review],
                            $position: 0
                        }
                    }
                }
            );

        if (result.matchedCount === 0) {
            return res.status(404).json({ error: "Listing not found." });
        }

        res.json({ message: "Review added successfully." });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

exports.addAmenity = async (req, res) => {
    try {
        const id = req.params.id;
        const { amenity } = req.body;

        if (!amenity || typeof amenity !== 'string') {
            return res.status(400).json({ error: "Amenity must be a non-empty string." });
        }

        const result = await getDB()
            .collection('listingsAndReviews')
            .updateOne(
                { _id: id },
                { $addToSet: { amenities: amenity } }
            );

        if (result.matchedCount === 0) {
            return res.status(404).json({ error: "Listing not found." });
        }

        res.json({ message: "Amenity added successfully." });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

exports.removeAmenity = async (req, res) => {
    try {
        const id = req.params.id;
        const { amenity } = req.body;

        if (!amenity || typeof amenity !== 'string') {
            return res.status(400).json({ error: "Amenity must be a non-empty string." });
        }

        const result = await getDB()
            .collection('listingsAndReviews')
            .updateOne(
                { _id: id },
                { $pull: { amenities: amenity } }
            );

        if (result.matchedCount === 0) {
            return res.status(404).json({ error: "Listing not found." });
        }

        res.json({ message: "Amenity removed successfully." });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Calculate average price using aggregation
exports.getAveragePrice = async (req, res) => {
    try {
        const result = await getDB().collection('listingsAndReviews')
            .aggregate([
                {$match: {price: {$exists: true}}}, // only docs with price
                {$group: {_id: null, avgPrice: {$avg: "$price"}}}
            ]).toArray();
        res.json({averagePrice: result[0]?.avgPrice || 0});
    } catch (err) {
        res.status(500).json({error: err.message});
    }
};

// Count all documents
exports.getListingsCount = async (req, res) => {
    try {
        const count = await getDB().collection('listingsAndReviews').countDocuments();
        res.json({count});
    } catch (err) {
        res.status(500).json({error: err.message});
    }
};

// Return 1 random listing using aggregation
exports.getRandomListing = async (req, res) => {
    try {
        const result = await getDB().collection('listingsAndReviews')
            .aggregate([{$sample: {size: 1}}]).toArray(); // $sample = random
        res.json(result[0] || {});
    } catch (err) {
        res.status(500).json({error: err.message});
    }
};

// Return listing filtered by number of beds and/or number of rooms and/or type o building
exports.filterListings = async (req, res) => {
    try {
        const { beds, bedrooms, type, market, amenity, page = 1 } = req.query;
        const pageSize = 10;

        const filter = {};

        if (beds) filter.beds = parseInt(beds);
        if (bedrooms) filter.bedrooms = parseInt(bedrooms);
        if (type) filter.property_type = type;
        if (market) filter["address.market"] = market;
        if (amenity) filter.amenities = amenity; // dopasowuje jeśli jest w tablicy amenities

        const collection = getDB().collection('listingsAndReviews');

        const totalCount = await collection.countDocuments(filter);
        const totalPages = Math.ceil(totalCount / pageSize);

        const listings = await collection
            .find(filter)
            .skip((page - 1) * pageSize)
            .limit(pageSize)
            .toArray();

        res.json({
            currentPage: parseInt(page),
            totalPages,
            totalCount,
            listings
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

function flattenObject(obj, prefix = '') {
    let fields = [];

    for (const key in obj) {
        const value = obj[key];
        const path = prefix ? `${prefix}.${key}` : key;

        // ✅ Dodajemy zawsze pole nadrzędne (niezależnie od typu)
        fields.push(path);

        if (value && typeof value === 'object') {
            // BSON typu Decimal128/ObjectId — nie rozwijamy
            if (value._bsontype) continue;

            if (Array.isArray(value)) {
                // Tablica obiektów
                if (value.length > 0 && typeof value[0] === 'object' && !Array.isArray(value[0])) {
                    continue; // np. reviews — nie rozwijamy głębiej
                } else {
                    continue; // np. amenities — już dodane
                }
            }

            // Rekurencja — rozwijamy dalej np. address
            fields = fields.concat(flattenObject(value, path));
        }
    }

    return fields;
}

exports.getFieldStats = async (req, res) => {
    try {
        const collection = getDB().collection('listingsAndReviews');
        const cursor = collection.find({});
        const total = await collection.estimatedDocumentCount();

        const fieldCounter = {};

        await cursor.forEach(doc => {
            const flatDoc = flattenObject(doc);
            // Zliczamy każde pole maks. raz na dokument
            new Set(flatDoc).forEach(key => {
                fieldCounter[key] = (fieldCounter[key] || 0) + 1;
            });
        });

        const fields = Object.entries(fieldCounter)
            .sort((a, b) => b[1] - a[1])
            .map(([field, count]) => ({
                field,
                count,
                percentage: ((count / total) * 100).toFixed(2) + '%'
            }));

        res.json({ totalDocuments: total, fields });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};