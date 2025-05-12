"""Command to generate example data for the example app."""

import datetime
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from example_project.example.models import (
    Article,
    ArticlePriority,
    ArticleStatus,
    Author,
    Category,
    Edition,
    EmbargoRegion,
    Magazine,
    PublishingMarket,
)


class Command(BaseCommand):
    """Command to generate example data for the example app."""

    help = "Generates example data for all models in the example app"

    def handle(self, *args, **options):
        """Generate example data for all models in the example app."""
        self.stdout.write("Generating example data...")

        # Clear existing data
        self.stdout.write("Clearing existing data...")
        Magazine.objects.all().delete()
        Edition.objects.all().delete()
        Category.objects.all().delete()
        Author.objects.all().delete()
        Article.objects.all().delete()
        PublishingMarket.objects.all().delete()
        EmbargoRegion.objects.all().delete()

        # Create Publishing Markets
        self.stdout.write("Creating publishing markets...")

        # Create regions
        regions = {
            "North America": {
                "United States": [
                    "New York",
                    "Los Angeles",
                    "Chicago",
                    "San Francisco",
                    "Boston",
                    "Seattle",
                ],
                "Canada": ["Toronto", "Vancouver", "Montreal"],
                "Mexico": ["Mexico City", "Guadalajara", "Monterrey"],
            },
            "Europe": {
                "United Kingdom": [
                    "London",
                    "Manchester",
                    "Edinburgh",
                    "Birmingham",
                    "Bristol",
                    "Glasgow",
                ],
                "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg"],
                "France": ["Paris", "Lyon", "Marseille"],
                "Spain": ["Madrid", "Barcelona", "Valencia"],
                "Italy": ["Rome", "Milan", "Florence"],
                "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht", "Eindhoven"],
                "Switzerland": ["Zurich", "Geneva", "Bern"],
                "Sweden": ["Stockholm", "Gothenburg"],
                "Norway": ["Oslo", "Bergen"],
            },
            "Asia Pacific": {
                "Japan": ["Tokyo", "Osaka", "Kyoto"],
                "China": ["Beijing", "Shanghai", "Guangzhou", "Hong Kong"],
                "South Korea": ["Seoul", "Busan"],
                "Australia": ["Sydney", "Melbourne", "Brisbane"],
                "India": ["Mumbai", "New Delhi", "Bangalore", "Hyderabad", "Chennai"],
                "Singapore": ["Singapore City"],
                "Malaysia": ["Kuala Lumpur", "Penang", "Johor Bahru"],
                "Thailand": ["Bangkok", "Chiang Mai"],
                "Vietnam": ["Ho Chi Minh City", "Hanoi"],
                "Philippines": [
                    "Manila",
                    "Cebu",
                    "Davao",
                    "Quezon",
                    "Makati",
                    "Pasig",
                    "Malaybalay",
                    "Taguig",
                ],
            },
            "Middle East": {
                "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah"],
                "Saudi Arabia": ["Riyadh", "Jeddah", "Mecca"],
                "Turkey": ["Istanbul", "Ankara", "Izmir"],
            },
            "Antarctica": {
                "Antarctica": ["McMurdo Station", "Amundsen-Scott South Pole Station"],
            },
        }

        # Create the hierarchy with realistic market sizes and publication counts
        for region_name, countries in regions.items():
            # Create region
            region = PublishingMarket.objects.create(
                name=region_name,
                market_size=0,  # Will be updated with sum of children
                active_publications=0,  # Will be updated with sum of children
            )
            self.stdout.write(f"Created region: {region_name}")

            for country_name, cities in countries.items():
                # Create country with randomized base metrics
                country_market_size = random.randint(20, 100)  # Millions of potential readers
                country_publications = random.randint(50, 200)

                country = PublishingMarket.objects.create(
                    name=country_name,
                    parent=region,
                    market_size=country_market_size,
                    active_publications=country_publications,
                )
                self.stdout.write(f"Created country: {country_name}")

                for city in cities:
                    # Create city/market with portion of country's metrics
                    city_market_size = int(country_market_size * random.uniform(0.1, 0.4))
                    city_publications = int(country_publications * random.uniform(0.1, 0.4))

                    PublishingMarket.objects.create(
                        name=city,
                        parent=country,
                        market_size=city_market_size,
                        active_publications=city_publications,
                    )
                    self.stdout.write(f"Created local market: {city}")

        # Create EmbargoRegions
        embargo_regions_data = [
            ("European Embargo", 1, "Digital-only embargo restrictions apply", 3),
            (
                "Asia-Pacific Embargo",
                2,
                "Limited content access before full embargo lift",
                7,
            ),
            (
                "North American Embargo",
                3,
                "Restrict all publications until the embargo period ends",
                10,
            ),
            (
                "South American Embargo",
                4,
                "Limited access to digital content during embargo",
                5,
            ),
            (
                "African Embargo",
                5,
                "No access to digital or print content during embargo",
                14,
            ),
            (
                "Middle East Embargo",
                6,
                "No access to digital or print content during embargo",
                14,
            ),
            (
                "Oceania Embargo",
                7,
                "Limited access to digital content during embargo",
                7,
            ),
            (
                "Antarctic Embargo",
                8,
                "No access to digital or print content during embargo",
                30,
            ),
        ]

        for name, tier, restrictions, days in embargo_regions_data:
            EmbargoRegion.objects.create(
                name=name,
                market_tier=tier,
                content_restrictions=restrictions,
                typical_embargo_days=days,
            )

        # Create magazines
        self.stdout.write("Creating magazines...")
        magazines = []
        magazine_names = [
            "Tech Today",
            "Awesome Django",
            "Science Monthly",
            "Digital Digest",
            "Code Review",
            "Data World",
            "Top Notch Django",
            "AI Insights",
            "Web Weekly",
            "Python Programming",
            "DevOps Digest",
            "Cloud Computing",
            "Mobile Tech Review",
            "Security Focus",
            "Enterprise Solutions",
            "Startup Weekly",
            "Innovation Quarterly",
            "Database Journal",
            "Network News",
            "Software Engineering Times",
            "UX Magazine",
            "API World",
            "Linux Journal",
            "Windows Tech",
            "Mac Developer Monthly",
            "Django Digest",
            "Cross-Platform Quarterly",
            "Gaming Technology",
            "Virtual Reality World",
            "IoT Insights",
            "Blockchain Review",
            "Quantum Computing Today",
            "Green Tech Magazine",
            "Future Tech",
            "Hardware Review",
            "System Architecture Digest",
            "Django Today",
            "Testing Times",
            "Agile Monthly",
            "Project Management Today",
            "Tech Leadership",
            "Digital Marketing Tech",
            "E-commerce Solutions",
            "Business Intelligence",
            "Machine Learning Journal",
            "Data Science Review",
            "Analytics Today",
            "Untangled Web",
            "Mobile Design Trends",
            "Design Systems Review",
            "UX Research Quarterly",
            "Color Theory Today",
            "Typography Trends",
            "Interaction Design Insights",
            "Responsive Design Review",
            "User Testing Journal",
            "Spaghetti Code Weekly",
            "Boring Code Monthly",
        ]
        for name in magazine_names:
            magazine = Magazine.objects.create(
                name=name,
                accepts_new_articles=random.choice(Magazine.AcceptsNewArticles.values),
            )
            magazines.append(magazine)
            self.stdout.write(f"Created magazine: {magazine.name}")

        # Create categories with hierarchy
        self.stdout.write("Creating categories...")
        main_categories = {
            "Development": [
                "Web Frontend",
                "Web Backend",
                "Mobile iOS",
                "Mobile Android",
                "Desktop Applications",
                "Cross-Platform",
                "Game Development",
                "Embedded Systems",
                "Systems Programming",
                "DevOps Practices",
                "Software Engineering",
                "Programming Languages",
                "Algorithms",
                "Data Structures",
                "Code Quality",
                "Testing",
                "Performance",
                "Serverless",
                "Containers",
            ],
            "Data": [
                "Analytics",
                "Machine Learning",
                "Big Data",
                "Data Visualization",
                "Data Engineering",
                "Business Intelligence",
                "Data Mining",
                "Statistical Analysis",
                "Predictive Modeling",
                "Data Warehousing",
                "ETL Pipelines",
                "Data Governance",
                "Data Privacy",
                "Data Ethics",
                "Natural Language Processing",
                "Computer Vision",
                "Deep Learning",
                "Reinforcement Learning",
                "Recommendation Systems",
                "Time Series",
                "Anomaly Detection",
                "Clustering",
                "Classification",
                "Regression",
            ],
            "Infrastructure": [
                "Access Control",
                "API Design",
                "Automation",
                "Caching",
                "CI/CD",
                "Clean Architecture",
                "Cloud Services",
                "Compliance",
                "Consistency",
                "Containerization",
                "Cost Optimization",
                "CQRS",
                "Data Partitioning",
                "Databases",
                "DevOps Tools",
                "Disaster Recovery",
                "Distributed Systems",
                "Domain-Driven",
                "Event Sourcing",
                "Event-Driven",
                "Fault Tolerance",
                "Firewalls",
                "Governance",
                "High Availability",
                "Infrastructure as Code",
                "Integration Patterns",
                "Intrusion Detection",
                "Kubernetes",
                "Latency",
                "Load Balancing",
                "Microservices",
                "Monitoring",
                "Networking",
                "Performance",
                "Reliability",
                "Resilience",
                "Scalability",
                "Security",
                "Server Management",
                "Service Mesh",
                "SOA",
                "Storage Solutions",
                "Throughput",
                "Virtualization",
            ],
            "Design": [
                "UI Design",
                "UX Research",
                "Visual Design",
                "Motion Design",
                "Design Systems",
                "Typography",
                "Color Theory",
                "Interaction Design",
                "Responsive Design",
                "Accessibility",
                "User Testing",
                "Wireframing",
                "Prototyping",
                "Design Thinking",
                "Design Patterns",
                "Design Critique",
                "User-Centered Design",
                "Information Architecture",
                "User Flows",
            ],
            "Web Frameworks": [
                "Django",
                "Flask",
                "FastAPI",
                "Tornado",
                "Falcon",
                "Sanic",
                "Bottle",
                "Pyramid",
                "CherryPy",
                "TurboGears",
                "Web2py",
                "Quart",
                "Starlette",
                "React",
                "Angular",
                "Vue.js",
                "Svelte",
                "Ember.js",
                "Backbone.js",
                "Meteor",
                "Polymer",
                "Aurelia",
                "Mithril",
                "Knockout",
            ],
            "Management": [
                "Agile",
                "Scrum",
                "Kanban",
                "Project Planning",
                "Team Leadership",
                "Risk Management",
                "Quality Assurance",
                "Resource Planning",
                "Technical Debt",
                "Change Management",
                "Stakeholder Management",
                "Conflict Resolution",
                "Decision Making",
                "Communication",
                "Feedback",
                "Mentoring",
                "Training",
                "Career Development",
                "Performance Reviews",
                "Goal Setting",
                "Motivation",
                "Employee Engagement",
                "Diversity & Inclusion",
                "Work-Life Balance",
                "Burnout Prevention",
                "Remote Work",
            ],
            "Security": [
                "Network Security",
                "Application Security",
                "Cryptography",
                "Identity Management",
                "Threat Analysis",
                "Security Operations",
                "Incident Response",
                "Penetration Testing",
                "Security Architecture",
                "Security Policies",
                "Security Awareness",
                "Vulnerability Management",
                "Security Audits",
                "Security Testing",
                "Security Automation",
                "Security Monitoring",
                "Security Tools",
                "Compliance Standards",
                "Data Protection",
                "Privacy Regulations",
                "Cybersecurity Threats",
                "Security Best Practices",
            ],
            "Emerging Tech": [
                "Artificial Intelligence",
                "Blockchain",
                "IoT",
                "Edge Computing",
                "Quantum Computing",
                "AR/VR",
                "5G Technology",
                "Robotics",
                "Biometrics",
                "Digital Twins",
                "Smart Cities",
                "Smart Homes",
                "Smart Grid",
                "Autonomous Vehicles",
                "Drones",
                "Wearables",
                "Voice Assistants",
                "Chatbots",
                "Digital Health",
                "Fintech",
            ],
            "Miscellaneous": [
                "General Programming",
                "Software Development",
                "Technology Trends",
                "Industry Insights",
                "Tutorials",
                "Opinion Pieces",
                "Interviews",
                "Book Reviews",
                "Podcast Transcripts",
                "Conference Reports",
                "Event Summaries",
                "Product Reviews",
                "Tool Reviews",
                "Framework Comparisons",
                "Language Comparisons",
                "Platform Comparisons",
                "Technology Reviews",
                "Vendor Comparisons",
                "Market Analysis",
                "Career Advice",
                "Job Postings",
                "Salary Reports",
                "Certification Guides",
                "Training Programs",
                "Research Papers",
                "Whitepapers",
                "Case Studies",
                "Use Cases",
                "Success Stories",
                "Failure Stories",
                "Lessons Learned",
                "Worst Practices",
                "Common Mistakes",
                "Avoiding Pitfalls",
                "Troubleshooting",
                "Debugging",
                "Performance Tuning",
                "Scaling",
                "Refactoring",
                "Rewriting",
                "Pair Programming",
                "Mob Programming",
                "Test-Driven Development",
                "Behavior-Driven Development",
                "Continuous Integration",
                "Continuous Deployment",
                "Continuous Testing",
                "Continuous Monitoring",
                "Feature Flags",
                "A/B Testing",
            ],
            "Office Life (empty category)": [],
            "Personal Development (empty category)": [],
            "Health & Wellness (empty category)": [],
            "Travel & Leisure (empty category)": [],
            "Food & Drink (empty category)": [],
        }

        categories = {}
        for main_cat, sub_cats in main_categories.items():
            parent = Category.objects.create(name=main_cat)
            categories[main_cat] = parent
            self.stdout.write(f"Created main category: {main_cat}")

            for sub_cat in sub_cats:
                child = Category.objects.create(name=sub_cat, parent=parent)
                categories[sub_cat] = child
                self.stdout.write(f"Created sub-category: {sub_cat}")

        # Create authors
        self.stdout.write("Creating authors...")
        authors = []
        with open(
            "example_project/example/management/commands/author_names.txt",
            encoding="utf-8",
        ) as f:
            author_names = [line.strip() for line in f.readlines()]

        bios = [
            "Expert in cloud computing and distributed systems with over 15 years of experience",
            "Specialist in data science and machine learning, focusing on practical applications",
            "Full-stack developer with extensive experience in web technologies and scalable systems",
            "Security researcher and DevOps practitioner specializing in automated security testing",
            "UI/UX designer and frontend developer with a passion for accessible design",
            "Data visualization expert and analytics consultant for Fortune 500 companies",
            "Mobile development specialist and app architect with focus on cross-platform solutions",
            "Infrastructure engineer specializing in cloud-native architectures",
            "Machine learning researcher with focus on natural language processing",
            "Blockchain developer and cryptocurrency expert",
            "DevOps engineer specializing in CI/CD pipelines and automation",
            "Backend developer focusing on high-performance distributed systems",
            "Frontend specialist with expertise in modern JavaScript frameworks",
            "Database administrator and performance optimization expert",
            "System architect with focus on scalable enterprise solutions",
            "Agile coach and technical project manager",
            "Quality assurance engineer specializing in automated testing",
            "Technical writer and documentation specialist",
            "API designer and integration specialist",
            "Software security analyst and penetration tester",
            "Network architect with expertise in SDN and cloud networking",
            "Embedded systems developer focusing on IoT solutions",
            "Game developer specializing in AR/VR technologies",
            "AI researcher focusing on computer vision applications",
            "Quantum computing researcher and algorithm specialist",
            "Big data engineer specializing in real-time processing systems",
            "UX researcher focusing on enterprise applications",
            "Performance optimization specialist",
            "Accessibility expert and inclusive design advocate",
            "Cloud security architect and compliance specialist",
            "Data privacy consultant and GDPR expert",
            "IT consultant and technology strategist",
            "Digital transformation specialist and innovation consultant",
            "Cybersecurity expert and threat analyst",
            "Software architect and design patterns enthusiast",
            "Open-source contributor and community leader",
            "Technology evangelist and conference speaker",
            "Startup advisor and mentor",
            "AI ethics researcher and bias mitigation specialist",
            "Blockchain consultant and smart contract developer",
            "IoT security specialist and privacy advocate",
            "Quantum cryptography researcher and encryption expert",
            "AR/VR designer focusing on immersive experiences",
            "5G technology expert and network infrastructure specialist",
            "Mundane author with no special skills or expertise",
            "Average developer with basic knowledge of programming",
            "Municipal worker with a passion for writing",
            "Unknown entity with no discernible qualities",
            "Java developer with a love for coffee and code",
            "Python programmer with a fondness for snakes",
            "C++ enthusiast with a penchant for performance",
            "JavaScript developer with a flair for frontend",
            "Ruby on Rails developer with a love for gems",
            "PHP programmer with a knack for WordPress",
            "Swift developer with a passion for iOS",
            "Kotlin developer with a love for Android",
            "Rust programmer with a focus on safety",
            "Go developer with a love for concurrency",
            "TypeScript developer with a passion for types",
            "Scala programmer with a flair for functional programming",
            "Haskell developer with a love for lambda calculus",
            "Clojure programmer with a focus on immutability",
            "Elixir developer with a passion for fault tolerance",
            "Dart programmer with a love for Flutter",
            "Objective-C developer with a focus on legacy code",
            "Assembly programmer with a passion for low-level",
            "COBOL developer with a love for mainframes",
            "Fortran programmer with a focus on scientific computing",
            "Pascal developer with a passion for teaching",
            "Lisp programmer with a love for parentheses",
            "Prolog developer with a focus on logic programming",
            "SQL programmer with a passion for databases",
            "NoSQL developer with a love for unstructured data",
            "GraphQL programmer with a focus on APIs",
            "Perl developer with a passion for regular expressions",
            "Bash programmer with a love for shell scripting",
        ]

        for name in author_names:
            bio = random.choice(bios)
            if random.random() < 0.3:  # 30% chance to combine two bios
                bio = f"{bio}. {random.choice(bios).lower()}"
            author = Author.objects.create(name=name, bio=bio)
            authors.append(author)
            self.stdout.write(f"Created author: {name}")

        # Create articles
        self.stdout.write("Creating articles...")

        with open("example_project/example/management/commands/article_titles.txt", encoding="utf-8") as f:
            title_templates = [line.strip() for line in f.readlines()]

        with open("example_project/example/management/commands/topics.txt", encoding="utf-8") as f:
            topics = [line.strip() for line in f.readlines()]

        status_weights = [
            (ArticleStatus.PUBLISHED, 0.6),
            (ArticleStatus.DRAFT, 0.2),
            (ArticleStatus.ARCHIVED, 0.15),
            (ArticleStatus.CANCELED, 0.05),
        ]
        priorities = [priority[0] for priority in ArticlePriority.choices]

        now = timezone.now()
        # Use a 2000-day window
        past_2000_days = now - datetime.timedelta(days=2000)
        total_seconds_2000_days = int((now - past_2000_days).total_seconds())

        for magazine in magazines:
            for year in range(2010, 2025):
                for month in range(1, 13):
                    name = f"{magazine.name} - {year}/{month:02d}"
                    Edition.objects.create(
                        name=name,
                        year=str(year),
                        pages=str(random.randint(40, 120)),
                        pub_num=f"PUB-{year}{month:02d}",
                        magazine=magazine,
                    )
                    self.stdout.write(f"Created edition: {name}")

            for _ in range(random.randint(50, 80)):
                article_authors = random.sample(authors, random.randint(1, 4))
                edition = Edition.objects.filter(magazine=magazine).order_by("?").first()

                # Select categories
                main_cat = random.choice(list(main_categories.keys()))
                sub_cats = main_categories[main_cat]
                selected_cats = [categories[main_cat]]
                num_sub_cats = random.randint(1, 2)
                self.stdout.write(f"Selected {num_sub_cats} sub-categories from {main_cat}")
                if len(sub_cats) < num_sub_cats:
                    num_sub_cats = len(sub_cats)
                # Randomly select sub-categories
                selected_sub_cats = random.sample(sub_cats, num_sub_cats)
                for sub_cat in selected_sub_cats:
                    selected_cats.append(categories[sub_cat])

                # Build title
                title_template = random.choice(title_templates)
                topic = random.choice(topics)
                year = random.randint(2020, 2024)
                if random.random() < 0.2:
                    topic = f"{topic} and {random.choice(topics)}"

                title = title_template.format(
                    topic=topic,
                    year=year,
                    tech=random.choice(topics),
                    domain=random.choice(topics),
                )

                status = random.choices(
                    [s[0] for s in status_weights],
                    weights=[s[1] for s in status_weights],
                )[0]
                priority = random.choice(priorities)
                word_count = random.randint(50, 2000)

                article = Article.objects.create(
                    title=title,
                    magazine=magazine,
                    edition=edition,
                    status=status,
                    priority=priority,
                    word_count=word_count,
                )

                article.authors.set(article_authors)
                article.categories.set(selected_cats)

                # Set random created_at and updated_at within last 2000 days
                created_at_offset = random.randint(0, total_seconds_2000_days)
                created_at = past_2000_days + datetime.timedelta(seconds=created_at_offset)

                # updated_at should be after created_at, but still within now
                # so we pick a random offset from created_at to now
                total_seconds_since_created = int((now - created_at).total_seconds())
                updated_at_offset = random.randint(0, total_seconds_since_created)
                updated_at = created_at + datetime.timedelta(seconds=updated_at_offset)

                article.created_at = created_at
                article.updated_at = updated_at
                article.save(update_fields=["created_at", "updated_at"])

                self.stdout.write(f"Created article: {title} (created_at={created_at}, updated_at={updated_at})")

        # After all articles are created, ensure each author's most recent article is unique
        # Get a list of all authors
        authors_list = list(Author.objects.all())
        # Sort authors by their name to have a deterministic order
        authors_list.sort(key=lambda a: a.name)

        # Nudge each author's most recent articles by a small delta to ensure uniqueness
        i = 0
        for _ in range(0, 5):
            for author in authors_list:
                most_recent_article = author.article_set.order_by("-updated_at").first()
                if most_recent_article:
                    # Subtract offset per author to ensure uniqueness
                    most_recent_article.created_at = most_recent_article.created_at - datetime.timedelta(days=i)
                    most_recent_article.updated_at = most_recent_article.updated_at - datetime.timedelta(days=i)

                    most_recent_article.save(update_fields=["created_at", "updated_at"])
                    i += 27  # increment by 27 days for each author

        self.stdout.write(self.style.SUCCESS("Successfully generated example data"))

        # Print summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Magazines: {Magazine.objects.count()}")
        self.stdout.write(f"Editions: {Edition.objects.count()}")
        self.stdout.write(f"Categories: {Category.objects.count()}")
        self.stdout.write(f"Authors: {Author.objects.count()}")
        self.stdout.write(f"Articles: {Article.objects.count()}")
        self.stdout.write(f"Embargo Regions: {EmbargoRegion.objects.count()}")
        self.stdout.write(f"Publishing Markets: {PublishingMarket.objects.count()}")
