def generate_deployments_from_prs(merged_prs: list):
    deployments = []
    for i, pr in enumerate(merged_prs):
        title = pr.get("title", "").lower()
        
        # Extract service from PR title if possible
        try:
            service = title.split("(")[1].split(")")[0] if "(" in title else "core"
        except:
            service = "core"

        # Determine status based on keywords
        if any(w in title for w in ["fix", "hotfix", "revert", "rollback"]):
            status = "hotfix"
        elif any(w in title for w in ["feat", "add", "new"]):
            status = "success"
        else:
            status = "success"

        deployments.append({
            "id": f"DEP-{i+1:03}",
            "service": service,
            "version": f"#{pr.get('number', '')}",
            "status": status,
            "environment": "production",
            "timestamp": pr.get("merged_at", ""),
            "deployed_by": "github-actions"
        })
    return deployments[:5]