# Ubernie Agents - 6 Only
# Do not add more agents without deleting one. 6 max.

1. sales-outbound-strategist.md -> Ollama: qwen2.5:14b -> Job: WhatsApp outreach to 1847 unclaimed
2. finance-fpa-analyst.md -> Ollama: qwen2.5:14b -> Job: Revenue Hunter, R-loss calc, audit score
3. support-support-responder.md -> Ollama: llama3.1:8b -> Job: Claim help, FAQ
4. marketing-content-creator.md -> Ollama: llama3.1:8b -> Job: Business description, WhatsApp bio
5. marketing-seo-specialist.md -> Ollama: llama3.1:8b -> Job: Google ranking, keywords for listing
6. product-manager.md -> Ollama: llama3.1:8b -> Job: What feature to build next

# Rules
- Sales + Finance use 14B (needs reasoning, money math)
- Support + Content + SEO + Product use 8B (fast, cheap)
- All agents read listings.json audit + revenue_hunter fields only. Never invent loss numbers.
