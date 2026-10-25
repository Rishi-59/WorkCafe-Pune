
from app import create_app
from app.extensions import db
from app.models import Area, Cafe


app = create_app()


AREAS = [
    {
        "name": "Model Colony",
        "slug": "model-colony",
    },
    {
        "name": "Kothrud",
        "slug": "kothrud",
    },
    {
        "name": "Bhoslenagar",
        "slug": "bhoslenagar",
    },
    {
        "name": "FC Road",
        "slug": "fc-road",
    },
    {
        "name": "Prabhat Road",
        "slug": "prabhat-road",
    },
    {
        "name": "Baner",
        "slug": "baner",
    },
    {
        "name": "Viman Nagar",
        "slug": "viman-nagar",
    },
    {
        "name": "Koregaon Park",
        "slug": "koregaon-park",
    },
]


# These are candidate listings, not verified recommendations.
# Confirm details before publishing them.
CAFES = [
    {
        "name": "The Third Space",
        "slug": "the-third-space",
        "area_slug": "model-colony",
    },
    {
        "name": "Waari Book Cafe",
        "slug": "waari-book-cafe",
        "area_slug": "kothrud",
    },
    {
        "name": "Mauji - The Time Cafe",
        "slug": "mauji-the-time-cafe",
        "area_slug": "bhoslenagar",
    },
    {
        "name": "Cafe Kathaa",
        "slug": "cafe-kathaa",
        "area_slug": "fc-road",
    },
    {
        "name": "Brewbox Blend Café + Cowork",
        "slug": "brewbox-blend-cafe-cowork",
        "area_slug": "prabhat-road",
    },
    {
        "name": "Qala Cafe and Co-works",
        "slug": "qala-cafe-and-co-works",
        "area_slug": "baner",
    },
    {
        "name": "Soch Et Latte",
        "slug": "soch-et-latte",
        "area_slug": "viman-nagar",
    },
    {
        "name": "Blue Tokai",
        "slug": "blue-tokai-koregaon-park",
        "area_slug": "koregaon-park",
    },
]


with app.app_context():
    # 1. Create areas that don't already exist.
    areas_created = 0

    for area_data in AREAS:
        existing_area = db.session.scalar(
            db.select(Area).where(Area.slug == area_data["slug"])
        )

        if existing_area is None:
            area = Area(**area_data)
            db.session.add(area)
            areas_created += 1

    # Flush pending area inserts so they can be queried below.
    db.session.flush()

    # 2. Create candidate cafes that don't already exist.
    cafes_created = 0

    for cafe_data in CAFES:
        existing_cafe = db.session.scalar(
            db.select(Cafe).where(Cafe.slug == cafe_data["slug"])
        )

        if existing_cafe is not None:
            continue

        area = db.session.scalar(
            db.select(Area).where(
                Area.slug == cafe_data["area_slug"]
            )
        )

        cafe = Cafe(
            name=cafe_data["name"],
            slug=cafe_data["slug"],
            address="Address to be verified",
            description=(
                "Candidate listing. Location details, facilities, "
                "and suitability for working need to be verified "
                "before publication."
            ),
            area=area,
            wifi_available=None,
            power_outlets=None,
            published=False,
        )

        db.session.add(cafe)
        cafes_created += 1

    # Commit all changes together.
    db.session.commit()

    print(f"Areas created: {areas_created}")
    print(f"Candidate cafes created: {cafes_created}")
    print("Seeding completed successfully.")
