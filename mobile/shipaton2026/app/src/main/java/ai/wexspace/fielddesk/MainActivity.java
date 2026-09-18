package ai.wexspace.fielddesk;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.io.InputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;

public final class MainActivity extends Activity {
    private static final int PICK_EVIDENCE_IMAGE = 201;

    private final List<EvidenceEntry> evidence = new ArrayList<>();
    private List<String> criteria = new ArrayList<>();
    private int pendingCriterionIndex = -1;

    private EditText workItem;
    private EditText objective;
    private EditText deliverable;
    private EditText criteriaInput;
    private TextView packageState;
    private TextView coverageState;
    private TextView billingState;
    private LinearLayout evidenceList;
    private Button addTextEvidence;
    private Button addImageEvidence;
    private Button runGate;
    private Button prepareReview;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
        restorePersistedPackage();
        refreshBilling();
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(7, 22, 18));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(22), dp(18), dp(40));
        scroll.addView(root);

        TextView brand = label("WEXSPACE FieldDesk", 26, true);
        brand.setTextColor(Color.rgb(123, 245, 194));
        root.addView(brand);

        TextView subtitle = label("Governed field evidence workbench", 14, false);
        subtitle.setTextColor(Color.LTGRAY);
        root.addView(subtitle);

        billingState = label("Billing: checking…", 13, false);
        billingState.setTextColor(Color.rgb(180, 220, 204));
        billingState.setPadding(0, dp(14), 0, dp(10));
        root.addView(billingState);

        LinearLayout billingActions = row();
        Button upgrade = button("Unlock Pro");
        upgrade.setOnClickListener(v -> RevenueCatManager.purchaseFirstPackage(this, this::showBillingResult));
        Button restore = button("Restore");
        restore.setOnClickListener(v -> RevenueCatManager.restore(this::showBillingResult));
        billingActions.addView(upgrade, weight());
        billingActions.addView(restore, weight());
        root.addView(billingActions);

        root.addView(sectionTitle("1 · Define the work"));
        workItem = input("Work item");
        objective = input("Objective");
        deliverable = input("Primary deliverable");
        criteriaInput = input("Acceptance criteria — one per line");
        criteriaInput.setMinLines(4);

        root.addView(workItem);
        root.addView(objective);
        root.addView(deliverable);
        root.addView(criteriaInput);

        Button create = button("Create / replace active work item");
        create.setOnClickListener(v -> createWorkItem());
        root.addView(create);

        packageState = label("No active package", 14, true);
        packageState.setTextColor(Color.WHITE);
        packageState.setPadding(0, dp(12), 0, dp(4));
        root.addView(packageState);

        coverageState = label("Coverage 0%", 13, false);
        coverageState.setTextColor(Color.rgb(123, 245, 194));
        root.addView(coverageState);

        root.addView(sectionTitle("2 · Add grounded evidence"));
        LinearLayout evidenceActions = row();
        addTextEvidence = button("Text evidence");
        addImageEvidence = button("Image evidence");
        addTextEvidence.setEnabled(false);
        addImageEvidence.setEnabled(false);
        addTextEvidence.setOnClickListener(v -> chooseCriterionForText());
        addImageEvidence.setOnClickListener(v -> chooseCriterionForImage());
        evidenceActions.addView(addTextEvidence, weight());
        evidenceActions.addView(addImageEvidence, weight());
        root.addView(evidenceActions);

        evidenceList = new LinearLayout(this);
        evidenceList.setOrientation(LinearLayout.VERTICAL);
        evidenceList.setPadding(0, dp(8), 0, dp(8));
        root.addView(evidenceList);

        root.addView(sectionTitle("3 · Deterministic gate"));
        runGate = button("Run evidence coverage gate");
        runGate.setEnabled(false);
        runGate.setOnClickListener(v -> runGate());
        root.addView(runGate);

        prepareReview = button("Prepare human review");
        prepareReview.setEnabled(false);
        prepareReview.setOnClickListener(v ->
                new AlertDialog.Builder(this)
                        .setTitle("Human release gate")
                        .setMessage("The package is prepared for human review. This app never auto-releases a package.")
                        .setPositiveButton("OK", null)
                        .show());
        root.addView(prepareReview);

        TextView footer = label(
                "Local-first MVP. Evidence coverage is computed deterministically; human authority remains the final release boundary.",
                12, false);
        footer.setTextColor(Color.GRAY);
        footer.setPadding(0, dp(20), 0, 0);
        root.addView(footer);

        return scroll;
    }

    private void createWorkItem() {
        criteria = GateEngine.parseCriteria(criteriaInput.getText().toString());
        if (workItem.getText().toString().trim().isEmpty() || criteria.isEmpty()) {
            Toast.makeText(this, "Enter a work item and at least one acceptance criterion.", Toast.LENGTH_LONG).show();
            return;
        }
        evidence.clear();
        evidenceList.removeAllViews();
        addTextEvidence.setEnabled(true);
        addImageEvidence.setEnabled(true);
        runGate.setEnabled(true);
        prepareReview.setEnabled(false);
        packageState.setText("ACTIVE · " + workItem.getText().toString().trim());
        updateCoverage();
        persistPackage();
    }

    private void chooseCriterionForText() {
        if (criteria.isEmpty()) return;
        final Spinner spinner = criterionSpinner();
        final EditText note = input("Evidence note / observation");
        LinearLayout box = dialogBox(spinner, note);
        new AlertDialog.Builder(this)
                .setTitle("Add text evidence")
                .setView(box)
                .setPositiveButton("Add", (d, w) -> {
                    String value = note.getText().toString().trim();
                    if (!value.isEmpty()) {
                        evidence.add(new EvidenceEntry(
                                spinner.getSelectedItemPosition(),
                                EvidenceEntry.Kind.TEXT,
                                value,
                                sha256(value.getBytes())
                        ));
                        renderEvidence();
                        updateCoverage();
                        persistPackage();
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void chooseCriterionForImage() {
        if (criteria.isEmpty()) return;
        final Spinner spinner = criterionSpinner();
        new AlertDialog.Builder(this)
                .setTitle("Attach image evidence")
                .setMessage("Choose which acceptance criterion this image supports.")
                .setView(spinner)
                .setPositiveButton("Choose image", (d, w) -> {
                    pendingCriterionIndex = spinner.getSelectedItemPosition();
                    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("image/*");
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                    startActivityForResult(intent, PICK_EVIDENCE_IMAGE);
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    @Override
    @SuppressWarnings("deprecation")
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_EVIDENCE_IMAGE || resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri uri = data.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (Exception ignored) {
        }
        String digest = hashUri(uri);
        evidence.add(new EvidenceEntry(pendingCriterionIndex, EvidenceEntry.Kind.IMAGE, uri.toString(), digest));
        pendingCriterionIndex = -1;
        renderEvidence();
        updateCoverage();
        persistPackage();
    }

    private void restorePersistedPackage() {
        WorkPackageStore.Snapshot snapshot = WorkPackageStore.load(this);
        if (snapshot == null) return;

        workItem.setText(snapshot.workItem);
        objective.setText(snapshot.objective);
        deliverable.setText(snapshot.deliverable);
        criteriaInput.setText(snapshot.criteriaRaw);
        criteria = GateEngine.parseCriteria(snapshot.criteriaRaw);

        if (snapshot.evidence != null) {
            evidence.clear();
            evidence.addAll(snapshot.evidence);
        }

        if (!snapshot.workItem.trim().isEmpty() && !criteria.isEmpty()) {
            addTextEvidence.setEnabled(true);
            addImageEvidence.setEnabled(true);
            runGate.setEnabled(true);
            packageState.setText("ACTIVE · " + snapshot.workItem.trim());
            renderEvidence();
            updateCoverage();
        }
    }

    private void persistPackage() {
        WorkPackageStore.save(
                this,
                workItem.getText().toString().trim(),
                objective.getText().toString().trim(),
                deliverable.getText().toString().trim(),
                criteriaInput.getText().toString(),
                evidence
        );
    }

    private void runGate() {
        GateEngine.GateResult result = GateEngine.evaluate(criteria, evidence);
        prepareReview.setEnabled(result.pass);
        new AlertDialog.Builder(this)
                .setTitle(result.pass ? "Gate PASS" : "Gate NOT YET PASS")
                .setMessage(result.message)
                .setPositiveButton("OK", null)
                .show();
    }

    private void renderEvidence() {
        evidenceList.removeAllViews();
        for (int i = 0; i < evidence.size(); i++) {
            EvidenceEntry item = evidence.get(i);
            String criterion = item.getCriterionIndex() >= 0 && item.getCriterionIndex() < criteria.size()
                    ? criteria.get(item.getCriterionIndex())
                    : "Unknown criterion";
            String hash = item.getSha256() == null ? "" : item.getSha256();
            if (hash.length() > 12) hash = hash.substring(0, 12) + "…";
            TextView row = label((i + 1) + ". " + item.getKind() + " → " + criterion + "\nSHA-256: " + hash, 12, false);
            row.setTextColor(Color.LTGRAY);
            row.setPadding(0, dp(6), 0, dp(6));
            evidenceList.addView(row);
        }
    }

    private void updateCoverage() {
        GateEngine.GateResult result = GateEngine.evaluate(criteria, evidence);
        int pct = result.total == 0 ? 0 : (int) Math.round((100.0 * result.covered) / result.total);
        coverageState.setText("Coverage " + pct + "% · " + result.covered + "/" + result.total + " criteria");
    }

    private void refreshBilling() {
        RevenueCatManager.refreshProStatus(this::showBillingResult);
    }

    private void showBillingResult(boolean pro, String message) {
        runOnUiThread(() -> {
            billingState.setText(message);
            billingState.setTextColor(pro ? Color.rgb(123, 245, 194) : Color.rgb(180, 220, 204));
        });
    }

    private Spinner criterionSpinner() {
        Spinner spinner = new Spinner(this);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, criteria);
        spinner.setAdapter(adapter);
        return spinner;
    }

    private LinearLayout dialogBox(View... views) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(20), dp(8), dp(20), 0);
        for (View view : views) {
            box.addView(view, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT));
        }
        return box;
    }

    private EditText input(String hint) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setTextColor(Color.WHITE);
        e.setHintTextColor(Color.GRAY);
        e.setBackgroundColor(Color.rgb(18, 48, 40));
        e.setPadding(dp(12), dp(10), dp(12), dp(10));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(0, dp(6), 0, dp(6));
        e.setLayoutParams(p);
        return e;
    }

    private TextView sectionTitle(String text) {
        TextView v = label(text, 16, true);
        v.setTextColor(Color.rgb(123, 245, 194));
        v.setPadding(0, dp(22), 0, dp(8));
        return v;
    }

    private TextView label(String text, int sp, boolean bold) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(sp);
        if (bold) v.setTypeface(null, android.graphics.Typeface.BOLD);
        return v;
    }

    private Button button(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        return b;
    }

    private LinearLayout row() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        return row;
    }

    private LinearLayout.LayoutParams weight() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        p.setMargins(dp(3), dp(3), dp(3), dp(3));
        return p;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private String hashUri(Uri uri) {
        try (InputStream in = getContentResolver().openInputStream(uri)) {
            if (in == null) return "";
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) > 0) digest.update(buffer, 0, n);
            return hex(digest.digest());
        } catch (Exception e) {
            return "";
        }
    }

    private String sha256(byte[] bytes) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return hex(digest.digest(bytes));
        } catch (Exception e) {
            return "";
        }
    }

    private String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format("%02x", b));
        return out.toString();
    }
}
