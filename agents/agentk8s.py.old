# File: agents/agentk8s.py

class AgentK8s:
    def __init__(self):
        self.objectives = None
        self.risks = []
        self.recommendations = []

    def set_objective(self, objective):
        self.objectives = objective

    def process_input(self, input_text):
        input_text = input_text.lower()

        if "pending pods" in input_text:
            self.risks.append("High pending pods")
            self.recommendations.append((
                "Review Cluster Autoscaler behavior", 
                "https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html"
            ))

        if "cpu" in input_text:
            self.risks.append("High CPU usage")
            self.recommendations.append((
                "Tune HPA thresholds or upgrade instance types",
                "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"
            ))

        if "memory" in input_text:
            self.risks.append("High memory consumption")
            self.recommendations.append((
                "Adjust pod memory limits/requests",
                "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
            ))

        return "Noted. Share more issues or click to generate the report."

    def generate_summary(self):
        summary = f"# EKS Operational Review\n\n"
        summary += f"### Objective\n{self.objectives}\n\n"
        summary += "### Risks\n"
        for r in self.risks:
            summary += f"- {r}\n"
        summary += "\n### Recommendations\n"
        for rec, link in self.recommendations:
            summary += f"- [{rec}]({link})\n"
        return summary
