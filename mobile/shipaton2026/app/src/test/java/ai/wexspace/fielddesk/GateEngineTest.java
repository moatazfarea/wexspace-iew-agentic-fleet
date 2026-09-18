package ai.wexspace.fielddesk;

import org.junit.Test;
import java.util.Arrays;
import java.util.List;
import static org.junit.Assert.*;

public final class GateEngineTest {
    @Test
    public void emptyCriteriaFailsClosed() {
        GateEngine.GateResult result = GateEngine.evaluate(Arrays.asList(), Arrays.asList());
        assertFalse(result.pass);
        assertEquals(0, result.total);
    }

    @Test
    public void partialCoverageDoesNotPass() {
        List<String> criteria = Arrays.asList("A", "B");
        List<EvidenceEntry> evidence = Arrays.asList(
                new EvidenceEntry(0, EvidenceEntry.Kind.TEXT, "proof", "hash")
        );
        GateEngine.GateResult result = GateEngine.evaluate(criteria, evidence);
        assertFalse(result.pass);
        assertEquals(1, result.covered);
        assertEquals(2, result.total);
    }

    @Test
    public void fullCoveragePasses() {
        List<String> criteria = Arrays.asList("A", "B");
        List<EvidenceEntry> evidence = Arrays.asList(
                new EvidenceEntry(0, EvidenceEntry.Kind.TEXT, "proof-a", "hash-a"),
                new EvidenceEntry(1, EvidenceEntry.Kind.IMAGE, "uri-b", "hash-b")
        );
        GateEngine.GateResult result = GateEngine.evaluate(criteria, evidence);
        assertTrue(result.pass);
        assertEquals(2, result.covered);
        assertEquals(2, result.total);
    }
}
