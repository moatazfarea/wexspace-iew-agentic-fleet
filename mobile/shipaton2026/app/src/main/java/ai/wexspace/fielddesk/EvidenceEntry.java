package ai.wexspace.fielddesk;

public final class EvidenceEntry {
    public enum Kind { TEXT, IMAGE }

    private final int criterionIndex;
    private final Kind kind;
    private final String value;
    private final String sha256;

    public EvidenceEntry(int criterionIndex, Kind kind, String value, String sha256) {
        this.criterionIndex = criterionIndex;
        this.kind = kind;
        this.value = value;
        this.sha256 = sha256;
    }

    public int getCriterionIndex() { return criterionIndex; }
    public Kind getKind() { return kind; }
    public String getValue() { return value; }
    public String getSha256() { return sha256; }
}
