from urllib.parse import urlparse
import mimetypes
from django.core.exceptions import ValidationError


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_MB = 5
MAX_URL_LENGTH = 2048


def validate_https_image_url(url):
	if not url:
		raise ValidationError("Image URL is required")
	if len(url) > MAX_URL_LENGTH:
		raise ValidationError("Image URL is too long")
	parsed = urlparse(url)
	if parsed.scheme.lower() != "https":
		raise ValidationError("Image URL must use https")

	path = (parsed.path or "").lower()
	if not any(path.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
		raise ValidationError("Image URL must end with a valid image extension")

	mime_type, _ = mimetypes.guess_type(parsed.path)
	if not mime_type or not mime_type.startswith("image/"):
		raise ValidationError("Image URL must point to an image")


def validate_uploaded_image(image_file):
	if not image_file:
		return
	max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
	if image_file.size > max_bytes:
		raise ValidationError("Image must be smaller than 5MB")
	content_type = getattr(image_file, "content_type", "")
	if content_type and not content_type.startswith("image/"):
		raise ValidationError("Uploaded file must be an image")
