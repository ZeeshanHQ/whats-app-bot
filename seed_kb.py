import asyncio
import logging
from app.services.ai_brain import ai_service
from app.services.db import seed_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_kb")

SEED_DOCUMENTS = [
    {
        "content": (
            "Astraventa is a premier Technology & AI Engineering Agency specializing in three main core areas: "
            "1. Agentic Automation Workflows & Enterprise Systems: Custom backend automation, multi-agent AI systems, high-concurrency data pipelines, microservices, and custom AI backends. "
            "2. Web Engineering & UI/UX: High-performance web application development, custom landing pages, Next.js / React / Vite frontend engineering, full-stack digital design, and responsive interfaces. "
            "3. WhatsApp & Communication Automation: Custom WhatsApp AI agents, VOIP phone routing, automated lead-capture chatbots, interactive button/list workflows, and Meta WhatsApp Cloud API integrations."
        ),
        "metadata": {"category": "company_overview"}
    },
    {
        "content": (
            "Astraventa Agentic Automation Workflows & Enterprise Backend Systems: "
            "We engineer autonomous AI agent systems, custom python backends, high-concurrency microservices, automated background task pipelines, database integrations (Supabase PostgreSQL, Vector RAG), and enterprise API routing."
        ),
        "metadata": {"category": "services_agentic_automation"}
    },
    {
        "content": (
            "Astraventa Web Engineering & UI/UX Design: "
            "We build modern, lightning-fast web applications, corporate websites, SaaS web portals, landing pages, interactive web dashboards, and mobile-first responsive interfaces using Next.js, React, HTML5, Vanilla CSS, Tailwind, and custom APIs."
        ),
        "metadata": {"category": "services_web_engineering"}
    },
    {
        "content": (
            "Astraventa WhatsApp & Communication Automation: "
            "We deploy production-grade WhatsApp AI engine solutions using Meta Cloud API v25.0, interactive quick-reply buttons, dynamic list menus, stateful conversation memory, lead qualification flows, and automated customer support routing."
        ),
        "metadata": {"category": "services_whatsapp_automation"}
    },
    {
        "content": (
            "Astraventa Pricing & Packages: "
            "1. Starter Automation Plan: $499/month (includes up to 5,000 automated messages, standard AI agent, and email support). "
            "2. Enterprise Automation Plan: $1,499/month (includes unlimited messages, custom RAG vector search, dedicated agentic workflow design, full CRM integration, custom web engineering, and 24/7 priority SLA support). "
            "3. Custom Consulting: Tailored quotes available for bespoke enterprise software builds."
        ),
        "metadata": {"category": "pricing"}
    },
    {
        "content": (
            "Contact & Booking Consultation for Astraventa: "
            "Book a 15-minute strategy call at https://astraventa.com/book | Email: contact@astraventa.com | Website: https://astraventa.com | Support WhatsApp: +1 (555) 153-2305."
        ),
        "metadata": {"category": "contact_info"}
    }
]


async def run_seeding():
    logger.info("Starting knowledge base seeding into Supabase...")
    for doc in SEED_DOCUMENTS:
        content = doc["content"]
        metadata = doc["metadata"]

        # Generate embedding vector
        embedding = await ai_service.generate_embedding(content)
        if not embedding:
            logger.warning(f"Failed to generate embedding for: {content[:30]}... Generating dummy vector for testing.")
            embedding = [0.01] * 768

        await seed_knowledge_base(content=content, embedding=embedding, metadata=metadata)

    logger.info("Knowledge base seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_seeding())
