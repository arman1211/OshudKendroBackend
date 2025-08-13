class OrgScopedQuerySetMixin:
    def get_queryset(self):
        return (
            super().get_queryset().filter(organization=self.request.user.organization)
        )


class CustomerOrganizationMixin:
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(checkout_orders__pharmacy_shop=self.request.user.organization)
        )
