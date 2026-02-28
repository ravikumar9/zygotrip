"""
PHASE 10: Review System
Uses static seed ratings for display.
Format: "4★ Hotel" + "4.3 Excellent (109 reviews)"
Can later integrate Google API or other review sources.
"""
import logging

logger = logging.getLogger(__name__)


class ReviewService:
    """Provides review data with consistent formatting"""
    
    RATING_LABELS = {
        5: 'Excellent',
        4.5: 'Very Good',
        4: 'Good',
        3.5: 'Average',
        3: 'Below Average',
        2: 'Poor',
        1: 'Very Poor',
    }
    
    # Static seed ratings for properties (can be replaced with real reviews)
    SEED_RATINGS = {
        'coorg_grand_stay': {'rating': 4.3, 'reviews': 109, 'verified': 85},
        'stay_saver_deal': {'rating': 3.8, 'reviews': 56, 'verified': 42},
        'global_10_percent_off': {'rating': 4.1, 'reviews': 73, 'verified': 58},
    }
    
    @staticmethod
    def get_property_reviews(property_slug):
        """
        Get reviews for property.
        
        Returns:
            {
                'property_slug': str,
                'rating': float,
                'rating_label': str,
                'review_count': int,
                'verified_reviews': int,
                'star_category': int,
                'display_text': str (e.g., "4.3 Excellent (109 reviews)"),
                'distribution': {...}  (star distribution)
            }
        """
        # TODO: Load from database when real reviews available
        seed_data = ReviewService.SEED_RATINGS.get(property_slug.lower(), None)
        
        if seed_data:
            rating = seed_data['rating']
            reviews = seed_data['reviews']
        else:
            # For unknown properties, use moderate defaults
            rating = 3.5
            reviews = 0
        
        star_category = int(round(rating))
        rating_label = ReviewService._get_rating_label(rating)
        
        return {
            'property_slug': property_slug,
            'rating': rating,
            'rating_label': rating_label,
            'review_count': reviews,
            'verified_reviews': seed_data.get('verified_reviews', 0) if seed_data else 0,
            'star_category': star_category,
            'display_text': f"{rating}★ {rating_label} ({reviews} reviews)",
            'display_text_short': f"{rating}★ {rating_label}",
            'distribution': ReviewService._get_rating_distribution(rating, reviews),
            'source': 'seed' if seed_data else 'no_reviews',
        }
    
    @staticmethod
    def _get_rating_label(rating):
        """Get human-readable label for rating"""
        for threshold in sorted(ReviewService.RATING_LABELS.keys(), reverse=True):
            if rating >= threshold:
                return ReviewService.RATING_LABELS[threshold]
        return 'No Rating'
    
    @staticmethod
    def _get_rating_distribution(rating, total_reviews):
        """
        Get approximate distribution of reviews by star.
        Used to show star breakdown on property detail page.
        
        Returns: {5: count, 4: count, 3: count, 2: count, 1: count}
        """
        if total_reviews == 0:
            return {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        
        # Approximate distribution based on overall rating
        # This is a heuristic; real data would come from review database
        distribution = {
            5: int(total_reviews * 0.40) if rating >= 4 else int(total_reviews * 0.20),
            4: int(total_reviews * 0.30) if rating >= 3.5 else int(total_reviews * 0.30),
            3: int(total_reviews * 0.20) if rating >= 3 else int(total_reviews * 0.30),
            2: int(total_reviews * 0.08) if rating < 3 else int(total_reviews * 0.10),
            1: int(total_reviews * 0.02) if rating < 2 else int(total_reviews * 0.05),
        }
        
        # Ensure counts add up to total
        total = sum(distribution.values())
        if total != total_reviews:
            diff = total_reviews - total
            distribution[5] += diff  # Add remainder to 5-star
        
        return distribution
    
    @staticmethod
    def get_all_property_reviews(properties_qs):
        """
        Get reviews for multiple properties.
        
        Args:
            properties_qs: QuerySet of Property objects
            
        Returns: [{property review data}, ...]
        """
        reviews = []
        
        for prop in properties_qs:
            review_data = ReviewService.get_property_reviews(prop.slug)
            reviews.append({
                'property_id': prop.id,
                'property_slug': prop.slug,
                'property_name': prop.name,
                **review_data
            })
        
        return reviews
    
    @staticmethod
    def format_review_badge(property_slug):
        """
        Format review badge for display on listing card.
        Returns HTML-safe string like "4.3★ (109)"
        """
        review_data = ReviewService.get_property_reviews(property_slug)
        
        if review_data['review_count'] == 0:
            return f"{review_data['rating_label']}"
        
        return f"{review_data['rating']}★ ({review_data['review_count']})"
    
    @staticmethod
    def format_review_detail(property_slug):
        """
        Format detailed review for property detail page.
        Returns string like "4.3 Excellent (109 reviews, 85 verified)"
        """
        review_data = ReviewService.get_property_reviews(property_slug)
        
        if review_data['review_count'] == 0:
            return "No reviews yet"
        
        verified_text = f", {review_data['verified_reviews']} verified" \
            if review_data['verified_reviews'] > 0 else ""
        
        return (
            f"{review_data['rating']} {review_data['rating_label']} "
            f"({review_data['review_count']} reviews{verified_text})"
        )
    
    @staticmethod
    def create_user_review(property_slug, user, rating, title, text):
        """
        Create a user review (future enhancement).
        Currently just logs - real implementation would save to database.
        """
        logger.info(
            f"Review created: {property_slug} by {user.username}: "
            f"{rating}★ - {title}"
        )
        
        # TODO: Save to Review model when available
        return {
            'status': 'pending',
            'message': 'Your review has been submitted for approval'
        }
