"""Validators for hotels app models."""

from django.core.exceptions import ValidationError


def validate_https_image_url(value):
    """Validate that URL is HTTPS and ends with valid image extension."""
    if not value:
        return
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
    
    if not value.startswith('https://'):
        raise ValidationError('Image URL must start with https://')
    
    # Check if URL ends with valid extension (ignoring query params)
    url_without_params = value.split('?')[0] if '?' in value else value
    
    if not any(url_without_params.lower().endswith(ext) for ext in valid_extensions):
        raise ValidationError(
            'Image URL must end with a valid image extension: ' + ', '.join(valid_extensions)
        )
