package ai.wexspace.fielddesk;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class GateEngine {
    private GateEngine() {}

    public static List<String> parseCriteria(String raw) {
        List<String> out = new ArrayList<>();
        if (raw == null) return out;
        for (String line : raw.split("\n")) {
            String cleaned = line.trim();
            if (!cleaned.isEmpty()) out.add(cleaned);
        }
        return out;
    }

    public static GateResult evaluate(List<String> criteria, List<EvidenceEntry> evidence) {
        if (criteria == null || criteria.isEmpty()) {
            return new GateResult(false, 0, 0, "Add at least one acceptance criterion.");
        }
        Set<Integer> covered = new HashSet<>();
        if (evidence != null) {
            for (EvidenceEntry item : evidence) {
                if (item.getCriterionIndex() >= 0 && item.getCriterionIndex() < criteria.size()) {
                    covered.add(item.getCriterionIndex());
                }
            }
        }
        boolean pass = covered.size() == criteria.size();
        String message = pass
                ? "All acceptance criteria have evidence. Human release is still required."
                : "Evidence coverage incomplete: " + covered.size() + "/" + criteria.size() + " criteria covered.";
        return new GateResult(pass, covered.size(), criteria.size(), message);
    }

    public static final class GateResult {
        public final boolean pass;
        public final int covered;
        public final int total;
        public final String message;

        public GateResult(boolean pass, int covered, int total, String message) {
            this.pass = pass;
            this.covered = covered;
            this.total = total;
            this.message = message;
        }
    }
}
