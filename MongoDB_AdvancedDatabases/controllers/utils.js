function buildOptionalFields({
                                 description,
                                 summary,
                                 space,
                                 neighborhood_overview,
                                 notes,
                                 transit,
                                 access,
                                 interaction,
                                 bed_type,
                                 last_scraped,
                                 calendar_last_scraped,
                                 accommodates,
                                 extra_people,
                                 guests_included,
                                 images,
                                 minimum_nights,
                                 maximum_nights,
                                 number_of_reviews,
                                 review_scores,
                                 reviews,
                                 first_review,
                                 last_review,
                                 cleaning_fee,
                                 security_deposit,
                                 weekly_price,
                                 beds,
                                 bedrooms,
                                 bathrooms,
                                 availability,
                                 listing_url,
                                 cancellation_policy,
                                 house_rules,
                                 location,
                             }) {
    const optionalFields = {};

    if (description) optionalFields.description = description;
    if (summary) optionalFields.summary = summary;
    if (space) optionalFields.space = space;
    if (neighborhood_overview) optionalFields.neighborhood_overview = neighborhood_overview;
    if (notes) optionalFields.notes = notes;
    if (transit) optionalFields.transit = transit;
    if (access) optionalFields.access = access;
    if (interaction) optionalFields.interaction = interaction;
    if (bed_type) optionalFields.bed_type = bed_type;
    if (last_scraped) optionalFields.last_scraped = last_scraped;
    if (calendar_last_scraped) optionalFields.calendar_last_scraped = calendar_last_scraped;
    if (!isNaN(Number(accommodates))) optionalFields.accommodates = Number(accommodates);
    if (!isNaN(Number(extra_people))) optionalFields.extra_people = Number(extra_people);
    if (!isNaN(Number(guests_included))) optionalFields.guests_included = Number(guests_included);

    if (images && typeof images === 'object') {
        optionalFields.images = {};
        if (typeof images.thumbnail_url === 'string') optionalFields.images.thumbnail_url = images.thumbnail_url;
        if (typeof images.medium_url === 'string') optionalFields.images.medium_url = images.medium_url;
        if (typeof images.picture_url === 'string') optionalFields.images.picture_url = images.picture_url;
        if (typeof images.xl_picture_url === 'string') optionalFields.images.xl_picture_url = images.xl_picture_url;
    }

    if (!isNaN(Number(minimum_nights))) optionalFields.minimum_nights = Number(minimum_nights);
    if (!isNaN(Number(maximum_nights))) optionalFields.maximum_nights = Number(maximum_nights);
    if (!isNaN(Number(number_of_reviews))) optionalFields.number_of_reviews = Number(number_of_reviews);

    if (Array.isArray(reviews)) optionalFields.reviews = reviews;
    if (review_scores && typeof review_scores === 'object') optionalFields.review_scores = review_scores;
    if (first_review) optionalFields.first_review = first_review;
    if (last_review) optionalFields.last_review = last_review;
    if (!isNaN(Number(cleaning_fee))) optionalFields.cleaning_fee = Number(cleaning_fee);
    if (!isNaN(Number(security_deposit))) optionalFields.security_deposit = Number(security_deposit);
    if (!isNaN(Number(weekly_price))) optionalFields.weekly_price = Number(weekly_price);

    if (!isNaN(Number(beds))) optionalFields.beds = Number(beds);
    if (!isNaN(Number(bedrooms))) optionalFields.bedrooms = Number(bedrooms);
    if (!isNaN(Number(bathrooms))) optionalFields.bathrooms = Number(bathrooms);

    if (availability && typeof availability === 'object') optionalFields.availability = availability;
    if (listing_url) optionalFields.listing_url = listing_url;
    if (cancellation_policy) optionalFields.cancellation_policy = cancellation_policy;
    if (house_rules) optionalFields.house_rules = house_rules;

    if (location?.longitude && location?.latitude) {
        const lng = parseFloat(location.longitude);
        const lat = parseFloat(location.latitude);
        if (!isNaN(lng) && !isNaN(lat)) {
            optionalFields.location = {
                type: "Point",
                coordinates: [lng, lat]
            };
        }
    }

    return optionalFields;
}

module.exports = { buildOptionalFields };
