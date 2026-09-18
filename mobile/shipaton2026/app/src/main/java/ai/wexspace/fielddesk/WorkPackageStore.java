package ai.wexspace.fielddesk;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public final class WorkPackageStore {
    private static final String PREFS = "wexspace_fielddesk";
    private static final String KEY = "active_package_v1";

    private WorkPackageStore() {}

    public static final class Snapshot {
        public final String workItem;
        public final String objective;
        public final String deliverable;
        public final String criteriaRaw;
        public final List<EvidenceEntry> evidence;

        Snapshot(String workItem, String objective, String deliverable, String criteriaRaw, List<EvidenceEntry> evidence) {
            this.workItem = workItem;
            this.objective = objective;
            this.deliverable = deliverable;
            this.criteriaRaw = criteriaRaw;
            this.evidence = evidence;
        }
    }

    public static void save(
            Context context,
            String workItem,
            String objective,
            String deliverable,
            String criteriaRaw,
            List<EvidenceEntry> evidence) {
        try {
            JSONObject root = new JSONObject();
            root.put("schema", 1);
            root.put("workItem", workItem);
            root.put("objective", objective);
            root.put("deliverable", deliverable);
            root.put("criteriaRaw", criteriaRaw);

            JSONArray items = new JSONArray();
            for (EvidenceEntry entry : evidence) {
                JSONObject item = new JSONObject();
                item.put("criterionIndex", entry.getCriterionIndex());
                item.put("kind", entry.getKind().name());
                item.put("value", entry.getValue());
                item.put("sha256", entry.getSha256());
                items.put(item);
            }
            root.put("evidence", items);

            prefs(context).edit().putString(KEY, root.toString()).apply();
        } catch (Exception ignored) {
        }
    }

    public static Snapshot load(Context context) {
        String raw = prefs(context).getString(KEY, null);
        if (raw == null || raw.trim().isEmpty()) return null;
        try {
            JSONObject root = new JSONObject(raw);
            if (root.optInt("schema", 0) != 1) return null;

            List<EvidenceEntry> evidence = new ArrayList<>();
            JSONArray items = root.optJSONArray("evidence");
            if (items != null) {
                for (int i = 0; i < items.length(); i++) {
                    JSONObject item = items.optJSONObject(i);
                    if (item == null) continue;
                    EvidenceEntry.Kind kind = EvidenceEntry.Kind.valueOf(item.optString("kind", "TEXT"));
                    evidence.add(new EvidenceEntry(
                            item.optInt("criterionIndex", -1),
                            kind,
                            item.optString("value", ""),
                            item.optString("sha256", "")
                    ));
                }
            }

            return new Snapshot(
                    root.optString("workItem", ""),
                    root.optString("objective", ""),
                    root.optString("deliverable", ""),
                    root.optString("criteriaRaw", ""),
                    evidence
            );
        } catch (Exception ignored) {
            return null;
        }
    }

    public static void clear(Context context) {
        prefs(context).edit().remove(KEY).apply();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
