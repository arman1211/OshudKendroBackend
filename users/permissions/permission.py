from rest_framework import permissions


class IsCompanyAdmin(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return request.user.role == "admin" and request.user.user_type == "company"


class IsBusinessAgent(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "business_agent"
            and request.user.user_type == "company"
        )


class IsOrganizationAdmin(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return request.user.role == "admin" and request.user.user_type == "organization"


class IsCompanyManager(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return request.user.role == "manager" and request.user.user_type == "company"


class IsOrganizationManager(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return (
            request.user.role == "manager" and request.user.user_type == "organization"
        )


class IsCompanyEmployee(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return request.user.role == "employee" and request.user.user_type == "company"


class IsOrganizationEmployee(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return (
            request.user.role == "employee" and request.user.user_type == "organization"
        )


class InventoryPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.user_type == "organization":
            if request.user.is_active == False:
                return False
            if request.user.role == "admin":
                return True
            if request.user.role == "manager" and request.method in [
                "GET",
                "POST",
                "PUT",
                "PATCH",
            ]:
                return True
            if request.user.role == "employee" and request.method in ["GET", "POST"]:
                return True
        else:
            return False


class CombinedPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        allowed_roles = [
            ("admin", "company"),
            ("manager", "company"),
            ("admin", "organization"),
            ("manager", "organization"),
            ("employee", "organization"),
        ]

        return (request.user.role, request.user.user_type) in allowed_roles
