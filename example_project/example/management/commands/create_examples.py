import random

from django.core.management.base import BaseCommand

from example_project.example.models import Article, Author, Category, Edition, Magazine


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

        # Create magazines
        self.stdout.write("Creating magazines...")
        magazines = []
        magazine_names = [
            "Tech Today",
            "Science Monthly",
            "Digital Digest",
            "Code Review",
            "Data World",
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
                "API Design",
                "Microservices",
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
                "Cloud Services",
                "Security",
                "Networking",
                "Storage Solutions",
                "Containerization",
                "Virtualization",
                "Kubernetes",
                "CI/CD",
                "Monitoring",
                "Load Balancing",
                "Databases",
                "Server Management",
                "Automation",
                "DevOps Tools",
                "Infrastructure as Code",
                "Disaster Recovery",
                "High Availability",
                "Scalability",
                "Performance",
                "Reliability",
                "Cost Optimization",
                "Compliance",
                "Governance",
                "Identity Management",
                "Access Control",
                "Firewalls",
                "Intrusion Detection",
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
            "Architecture": [
                "Microservices",
                "Serverless",
                "Event-Driven",
                "Domain-Driven",
                "Clean Architecture",
                "CQRS",
                "Event Sourcing",
                "SOA",
                "API Design",
                "Integration Patterns",
                "Service Mesh",
                "Distributed Systems",
                "Scalability",
                "Performance",
                "Reliability",
                "Security",
                "Resilience",
                "Fault Tolerance",
                "High Availability",
                "Consistency",
                "Latency",
                "Throughput",
                "Data Partitioning",
                "Caching",
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
                "Compliance",
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
                "Computer Vision",
                "Natural Language Processing",
                "Biometrics",
                "Digital Twins",
                "Smart Cities",
                "Smart Homes",
                "Smart Grid",
            ],
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
        with open("example_project/example/management/commands/author_names.txt", "r", encoding="utf-8") as f:
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
        with open("example_project/example/management/commands/article_titles.txt", "r", encoding="utf-8") as f:
            title_templates = [line.strip() for line in f.readlines()]

        with open("example_project/example/management/commands/topics.txt", "r", encoding="utf-8") as f:
            topics = [line.strip() for line in f.readlines()]

        status_weights = [(Article.Status.ACTIVE, 0.6), (Article.Status.DRAFT, 0.25), (Article.Status.ARCHIVED, 0.15)]

        for magazine in magazines:
            for year in range(2020, 2025):
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
                # Select random authors (1-4)
                article_authors = random.sample(authors, random.randint(1, 4))

                # Select a random Edition that belongs to this magazine
                edition = Edition.objects.filter(magazine=magazine).order_by("?").first()

                # Select random categories (1-3)
                main_cat = random.choice(list(main_categories.keys()))
                sub_cats = main_categories[main_cat]
                selected_cats = [categories[main_cat]]

                # Add 1-2 subcategories
                num_sub_cats = random.randint(1, 2)
                selected_sub_cats = random.sample(sub_cats, num_sub_cats)
                for sub_cat in selected_sub_cats:
                    selected_cats.append(categories[sub_cat])

                # Create article
                title_template = random.choice(title_templates)
                topic = random.choice(topics)
                year = random.randint(2020, 2024)

                # Sometimes combine topics
                if random.random() < 0.2:  # 20% chance to combine topics
                    topic = f"{topic} and {random.choice(topics)}"

                title = title_template.format(
                    topic=topic, year=year, tech=random.choice(topics), domain=random.choice(topics)
                )

                status = random.choices([s[0] for s in status_weights], weights=[s[1] for s in status_weights])[0]

                article = Article.objects.create(title=title, magazine=magazine, edition=edition, status=status)

                # Add relationships
                article.authors.set(article_authors)
                article.categories.set(selected_cats)

                self.stdout.write(f"Created article: {title}")

        self.stdout.write(self.style.SUCCESS("Successfully generated example data"))

        # Print summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Magazines: {Magazine.objects.count()}")
        self.stdout.write(f"Editions: {Edition.objects.count()}")
        self.stdout.write(f"Categories: {Category.objects.count()}")
        self.stdout.write(f"Authors: {Author.objects.count()}")
        self.stdout.write(f"Articles: {Article.objects.count()}")
