const LABELS = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

export const isActive = (status) => status === "pending" || status === "processing";

export const formatDate = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{LABELS[status] ?? status}</span>;
}
