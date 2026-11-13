from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from db.models import Base
from intelligence import create_source, queue_job, ingest_candidate


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def source(db, *, enabled=True):
    return create_source(
        db,
        name="Example business registry",
        base_url="https://directory.example.za",
        purpose="Discover publicly listed business details",
        terms_reviewed=True,
        collection_permitted=True,
        robots_reviewed=True,
        enabled=enabled,
        requests_per_minute=6,
        created_by="admin-1",
    )


def test_source_is_disabled_until_explicitly_approved(db):
    item = create_source(
        db,
        name="Unreviewed source",
        base_url="https://example.za",
        purpose="Review before any collection",
        terms_reviewed=False,
        collection_permitted=False,
        robots_reviewed=False,
        enabled=False,
        requests_per_minute=6,
        created_by="admin-1",
    )
    with pytest.raises(ValueError, match="missing or disabled"):
        queue_job(db, source_id=item.id, requested_url="https://example.za/list", created_by="admin-1")


def test_source_cannot_be_enabled_without_policy_reviews(db):
    with pytest.raises(ValueError, match="cannot be enabled"):
        create_source(
            db,
            name="Unreviewed source",
            base_url="https://example.za",
            purpose="Review before any collection",
            terms_reviewed=True,
            collection_permitted=False,
            robots_reviewed=True,
            enabled=True,
            requests_per_minute=6,
            created_by="admin-1",
        )


def test_source_rejects_non_https_url(db):
    with pytest.raises(ValueError, match="HTTPS"):
        create_source(
            db,
            name="Unsafe source",
            base_url="http://example.za",
            purpose="Test invalid scheme",
            terms_reviewed=True,
            collection_permitted=True,
            robots_reviewed=True,
            enabled=True,
            requests_per_minute=6,
            created_by="admin-1",
        )


def test_jobs_are_bound_to_registered_source_host(db):
    item = source(db)
    job = queue_job(
        db,
        source_id=item.id,
        requested_url="https://directory.example.za/businesses",
        created_by="admin-1",
    )
    assert job.status == "queued"
    with pytest.raises(ValueError, match="registered source host"):
        queue_job(
            db,
            source_id=item.id,
            requested_url="https://other.example.za/businesses",
            created_by="admin-1",
        )


def test_candidate_keeps_provenance_and_stays_pending_review(db):
    item = source(db)
    candidate, duplicate = ingest_candidate(
        db,
        source_id=item.id,
        source_url="https://directory.example.za/listing/alpha",
        business_name="Alpha Plumbing",
        created_fields={"city": "Johannesburg", "province": "Gauteng", "phone": "+27110000000"},
    )
    assert duplicate is False
    assert candidate.status == "pending_review"
    assert len(candidate.evidence) == 4
    assert all(row["source_url"] == "https://directory.example.za/listing/alpha" for row in candidate.evidence)


def test_duplicate_candidate_is_not_silently_merged_or_recreated(db):
    item = source(db)
    first, duplicate1 = ingest_candidate(
        db, source_id=item.id, source_url="https://directory.example.za/a",
        business_name="Alpha Plumbing", created_fields={"city": "Johannesburg"},
    )
    second, duplicate2 = ingest_candidate(
        db, source_id=item.id, source_url="https://directory.example.za/b",
        business_name="ALPHA PLUMBING", created_fields={"city": "Johannesburg"},
    )
    assert duplicate1 is False
    assert duplicate2 is True
    assert first.id == second.id
    assert second.status == "pending_review"


def test_same_name_same_city_different_official_domains_are_not_merged(db):
    item = source(db)
    first, duplicate1 = ingest_candidate(
        db, source_id=item.id, source_url="https://directory.example.za/a",
        business_name="Alpha Plumbing", created_fields={
            "city": "Johannesburg", "website": "https://alpha-one.example.za",
        },
    )
    second, duplicate2 = ingest_candidate(
        db, source_id=item.id, source_url="https://directory.example.za/b",
        business_name="Alpha Plumbing", created_fields={
            "city": "Johannesburg", "website": "https://alpha-two.example.za",
        },
    )
    assert duplicate1 is False
    assert duplicate2 is False
    assert first.id != second.id


def test_source_rejects_private_ip_literal(db):
    with pytest.raises(ValueError, match="Non-public IP"):
        create_source(
            db,
            name="Private target",
            base_url="https://127.0.0.1",
            purpose="Must not target local services",
            terms_reviewed=True,
            collection_permitted=True,
            robots_reviewed=True,
            enabled=True,
            requests_per_minute=1,
            created_by="admin-1",
        )


def test_source_rejects_nonstandard_https_ports(db):
    with pytest.raises(ValueError, match="port 443"):
        create_source(
            db,
            name="Nonstandard port",
            base_url="https://example.za:8443",
            purpose="Avoid arbitrary service ports",
            terms_reviewed=True,
            collection_permitted=True,
            robots_reviewed=True,
            enabled=True,
            requests_per_minute=1,
            created_by="admin-1",
        )
