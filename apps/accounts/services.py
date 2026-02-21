from .models import Role, UserRole


def assign_customer_role(user):
    role = Role.objects.filter(code='customer').first()
    if role:
        UserRole.objects.get_or_create(user=user, role=role)
    return role
