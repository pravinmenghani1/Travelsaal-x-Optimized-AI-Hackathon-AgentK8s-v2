import re

class AgentK8s:
    def __init__(self):
        self.objectives = None
        self.responses = []
        self.risks = []
        self.recommendations = []

    def process_input(self, input_text):
        self.responses.append(input_text)

        # Simple pattern matching to identify risks and recommendations
        if "pending pods" in input_text.lower() or "max pending pods" in input_text.lower():
            self.risks.append("High pending pods during peak hours")
            self.recommendations.append((
                "Ensure Cluster Autoscaler is tuned properly and nodes can be provisioned in time.",
                "https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html"
            ))

        if re.search(r"cpu.*(89|9\d)%", input_text.lower()):
            self.risks.append("High CPU utilization near limit")
            self.recommendations.append((
                "Consider increasing pod replicas or upgrading instance types.",
                "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"
            ))

        if re.search(r"memory.*(9\d)%", input_text.lower()):
            self.risks.append("High memory utilization near limit")
            self.recommendations.append((
                "Tune memory requests/limits and optimize application usage.",
                "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
            ))

        if "evicted" in input_text.lower():
            self.risks.append("Pods evicted due to memory pressure or scale-downs")
            self.recommendations.append((
                "Review eviction policies and ensure PodDisruptionBudgets are correctly applied.",
                "https://kubernetes.io/docs/tasks/run-application/configure-pdb/"
            ))

        if "latency" in input_text.lower() and "ms" in input_text.lower():
            self.risks.append("API latency spikes under load")
            self.recommendations.append((
                "Optimize service response time, autoscale latency-sensitive services.",
                "https://aws.amazon.com/blogs/containers/best-practices-for-observability-in-eks/"
            ))

        return "Noted! Do you want to describe another issue or generate the report?"

    def generate_summary(self):
        summary = "## EKS Operational Review\n"

        if self.objectives:
            summary += f"\n### Objective\n{self.objectives}\n"

        summary += "\n### Risks\n"
        if self.risks:
            for risk in set(self.risks):
                summary += f"- 🚨 {risk}\n"
        else:
            summary += "_No major risks detected based on input._\n"

        summary += "\n### Recommendations\n"
        if self.recommendations:
            for rec, link in self.recommendations:
                summary += f"- ✅ [{rec}]({link})\n"
        else:
            summary += "_No recommendations based on current inputs._\n"

        return summary
