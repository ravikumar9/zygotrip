from urllib.parse import urlparse
import mimetypes
from urllib.request import Request, urlopen
from django.core.exceptions import ValidationError


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_MB = 5


def validate_https_image_url(url):
	if not url:
		raise ValidationError("Image URL is required")
	parsed = urlparse(url)
	if parsed.scheme.lower() != "https":
		raise ValidationError("Image URL must use https")
	
	path = (parsed.path or "").lower()
	if not any(ext for ext in ALLOWED_IMAGE_EXTENSIONS if path.endswith(ext)):
		raise ValidationError("Image URL must end with a valid image extension")
	
	mime_type, _ = mimetypes.guess_type(parsed.path)
	if not mime_type or not mime_type.startswith("image/"):
		raise ValidationError("Image URL must point to an image")

	try:
		request = Request(url, method="HEAD")
		with urlopen(request, timeout=2) as response:
			content_length = response.headers.get("Content-Length")
			if content_length and int(content_length) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
				raise ValidationError("Image must be smaller than 5MB")
			content_type = response.headers.get("Content-Type") or ""
			if content_type and not content_type.startswith("image/"):
				raise ValidationError("Image URL must point to an image")
	except ValidationError:
		raise
	except Exception:
		# If remote headers are unavailable, keep URL validation but avoid blocking
		pass



def validate_uploaded_image(image_file):
	if not image_file:
		return
	max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
	if image_file.size > max_bytes:
		raise ValidationError("Image must be smaller than 5MB")
	content_type = getattr(image_file, "content_type", "")
	if content_type and not content_type.startswith("image/"):
		raise ValidationError("Uploaded file must be an image")
