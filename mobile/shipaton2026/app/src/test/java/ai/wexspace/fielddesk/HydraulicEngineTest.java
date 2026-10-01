package ai.wexspace.fielddesk;

import org.junit.Test;
import static org.junit.Assert.*;

public final class HydraulicEngineTest {
    @Test public void demoNetworkIsDeterministicAndIndependentlyVerified(){
        HydraulicEngine.Segment[] segments=HydraulicEngine.demoNetwork();
        assertEquals(3,segments.length);
        for(HydraulicEngine.Segment s:segments){
            HydraulicEngine.Result a=HydraulicEngine.calculate(s,false);
            HydraulicEngine.Result b=HydraulicEngine.calculate(s,false);
            HydraulicEngine.Result independent=HydraulicEngine.calculate(s,true);
            assertEquals(a.velocity,b.velocity,1e-12);
            assertEquals(a.dropKpa,b.dropKpa,1e-12);
            assertTrue(HydraulicEngine.verify(a,independent));
            assertTrue(a.velocity>0);
            assertTrue(a.reynolds>0);
        }
    }

    @Test public void endpointPressureStaysAboveDemoMinimum(){
        HydraulicEngine.Segment[] s=HydraulicEngine.demoNetwork();
        HydraulicEngine.Result r0=HydraulicEngine.calculate(s[0],false);
        HydraulicEngine.Result r1=HydraulicEngine.calculate(s[1],false);
        HydraulicEngine.Result r2=HydraulicEngine.calculate(s[2],false);
        assertTrue(450.0-r0.dropKpa-r1.dropKpa>=150.0);
        assertTrue(450.0-r0.dropKpa-r2.dropKpa>=150.0);
    }
}
