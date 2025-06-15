"""
Enhanced Search Utilities

Provides advanced search functionality for health records.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_

from ..models import HealthRecord, User


class HealthRecordSearcher:
    """Advanced search functionality for health records"""

    def __init__(self, user: User):
        self.user = user

    def search(
        self,
        query: str = "",
        record_type: Optional[str] = None,
        provider: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_family: bool = False,
        search_fields: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> tuple[list[HealthRecord], dict]:
        """
        Perform advanced search on health records

        Args:
            query: Search query string
            record_type: Filter by record type
            provider: Filter by provider
            date_from: Start date filter
            date_to: End date filter
            include_family: Include family member records
            search_fields: Specific fields to search in
            limit: Maximum number of results

        Returns:
            Tuple of (records, search_metadata)
        """
        # Start with base query
        base_query = HealthRecord.query

        # Filter by user/family
        if include_family:
            family_member_ids = [fm.id for fm in self.user.family_members]
            base_query = base_query.filter(
                or_(
                    HealthRecord.user_id == self.user.id,
                    HealthRecord.family_member_id.in_(family_member_ids),
                )
            )
        else:
            base_query = base_query.filter(
                HealthRecord.user_id == self.user.id,
                HealthRecord.family_member_id.is_(None),
            )

        # Apply filters
        if record_type:
            base_query = base_query.filter(HealthRecord.record_type == record_type)

        if provider:
            base_query = base_query.filter(HealthRecord.provider.ilike(f"%{provider}%"))

        if date_from:
            base_query = base_query.filter(HealthRecord.date >= date_from)

        if date_to:
            base_query = base_query.filter(HealthRecord.date <= date_to)

        # Apply text search
        if query:
            search_conditions = self._build_search_conditions(query, search_fields)
            base_query = base_query.filter(search_conditions)

        # Order by relevance and date
        base_query = base_query.order_by(HealthRecord.date.desc())

        # Apply limit
        if limit:
            base_query = base_query.limit(limit)

        records = base_query.all()

        # Generate search metadata
        metadata = self._generate_search_metadata(
            records,
            query,
            {
                "record_type": record_type,
                "provider": provider,
                "date_from": date_from,
                "date_to": date_to,
                "include_family": include_family,
            },
        )

        return records, metadata

    def _build_search_conditions(self, query: str, search_fields: Optional[list[str]]):
        """Build search conditions for the query"""
        search_terms = query.split()

        # Default search fields
        if not search_fields:
            search_fields = ["summary", "symptoms", "diagnosis", "treatment", "notes"]

        conditions = []

        for term in search_terms:
            term_conditions = []

            for field in search_fields:
                if hasattr(HealthRecord, field):
                    field_attr = getattr(HealthRecord, field)
                    term_conditions.append(field_attr.ilike(f"%{term}%"))

            if term_conditions:
                conditions.append(or_(*term_conditions))

        return and_(*conditions) if conditions else True

    def _generate_search_metadata(
        self, records: list[HealthRecord], query: str, filters: dict
    ) -> dict:
        """Generate metadata about the search results"""
        metadata = {
            "total_results": len(records),
            "query": query,
            "filters_applied": {k: v for k, v in filters.items() if v is not None},
            "search_time": datetime.now(),
            "record_types": {},
            "providers": {},
            "date_range": {},
        }

        if records:
            # Analyze record types
            for record in records:
                record_type = record.record_type or "Unknown"
                metadata["record_types"][record_type] = (
                    metadata["record_types"].get(record_type, 0) + 1
                )

            # Analyze providers
            for record in records:
                provider = record.provider or "Unknown"
                metadata["providers"][provider] = (
                    metadata["providers"].get(provider, 0) + 1
                )

            # Date range
            dates = [record.date for record in records if record.date]
            if dates:
                metadata["date_range"] = {"earliest": min(dates), "latest": max(dates)}

        return metadata

    def get_suggestions(self, partial_query: str, field: str = "all") -> list[str]:
        """Get search suggestions based on partial query"""
        suggestions = []

        if field in {"all", "provider"}:
            # Provider suggestions
            provider_query = (
                HealthRecord.query.filter(
                    HealthRecord.user_id == self.user.id,
                    HealthRecord.provider.ilike(f"%{partial_query}%"),
                )
                .with_entities(HealthRecord.provider)
                .distinct()
                .limit(5)
            )

            suggestions.extend([p.provider for p in provider_query if p.provider])

        if field in {"all", "record_type"}:
            # Record type suggestions
            type_query = (
                HealthRecord.query.filter(
                    HealthRecord.user_id == self.user.id,
                    HealthRecord.record_type.ilike(f"%{partial_query}%"),
                )
                .with_entities(HealthRecord.record_type)
                .distinct()
                .limit(5)
            )

            suggestions.extend([t.record_type for t in type_query if t.record_type])

        return list(set(suggestions))

    def get_search_statistics(self) -> dict:
        """Get statistics about searchable content"""
        user_records = HealthRecord.query.filter_by(user_id=self.user.id)

        stats = {
            "total_records": user_records.count(),
            "record_types": {},
            "providers": {},
            "recent_activity": {},
        }

        # Record types
        type_counts = (
            user_records.with_entities(
                HealthRecord.record_type, func.count(HealthRecord.id)
            )
            .group_by(HealthRecord.record_type)
            .all()
        )

        stats["record_types"] = {(rt or "Unknown"): count for rt, count in type_counts}

        # Providers
        provider_counts = (
            user_records.with_entities(
                HealthRecord.provider, func.count(HealthRecord.id)
            )
            .group_by(HealthRecord.provider)
            .all()
        )

        stats["providers"] = {(p or "Unknown"): count for p, count in provider_counts}

        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_count = user_records.filter(HealthRecord.date >= thirty_days_ago).count()

        stats["recent_activity"] = {"last_30_days": recent_count}

        return stats


def search_health_records(
    user: User, query: str = "", **kwargs
) -> tuple[list[HealthRecord], dict]:
    """Convenience function for searching health records"""
    searcher = HealthRecordSearcher(user)
    return searcher.search(query, **kwargs)
