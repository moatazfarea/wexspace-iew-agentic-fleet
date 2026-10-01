package ai.wexspace.fielddesk;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;

public final class EngineeringActivity extends Activity {
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(build());}
    private LinearLayout build(){
        ScrollView sc=new ScrollView(this);sc.setBackgroundColor(WexspaceBrand.BG);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(24),dp(20),dp(36));sc.addView(root);
        root.addView(text("←  ENGINEERING / UTL-NET-001",11,true,WexspaceBrand.CYAN));
        root.addView(text("Neutral Cooling-Water\nDistribution Network",30,true,WexspaceBrand.TEXT));
        TextView intro=text("Synthetic deterministic study · Swamee–Jain primary calculation · Haaland independent verification",13,false,WexspaceBrand.MUTED);intro.setPadding(0,dp(10),0,dp(18));root.addView(intro);

        double source=450.0;
        HydraulicEngine.Segment[] segs=HydraulicEngine.demoNetwork();
        HydraulicEngine.Result[] pri=new HydraulicEngine.Result[segs.length],ind=new HydraulicEngine.Result[segs.length];
        boolean verified=true;
        for(int i=0;i<segs.length;i++){pri[i]=HydraulicEngine.calculate(segs[i],false);ind[i]=HydraulicEngine.calculate(segs[i],true);verified&=HydraulicEngine.verify(pri[i],ind[i]);}

        LinearLayout receipt=card();receipt.setPadding(dp(16),dp(16),dp(16),dp(16));
        receipt.addView(text("EXECUTION RECEIPT",10,true,WexspaceBrand.CYAN));
        receipt.addView(text("Source pressure  "+fmt(source)+" kPa",14,true,WexspaceBrand.TEXT));
        receipt.addView(text("3 segments · water 25°C · user-supplied properties",12,false,WexspaceBrand.MUTED));
        TextView pass=text(verified?"✓ INDEPENDENT VERIFICATION PASS":"VERIFICATION REVIEW REQUIRED",13,true,verified?WexspaceBrand.GREEN:Color.rgb(255,120,120));pass.setPadding(0,dp(10),0,0);receipt.addView(pass);root.addView(receipt,margin(dp(0),0,0,dp(14)));

        for(int i=0;i<segs.length;i++){
            LinearLayout c=card();c.setPadding(dp(16),dp(16),dp(16),dp(16));
            c.addView(text(pri[i].id,10,true,WexspaceBrand.CYAN));
            c.addView(text("Velocity  "+fmt(pri[i].velocity)+" m/s",17,true,WexspaceBrand.TEXT));
            c.addView(text("Pressure drop  "+fmt(pri[i].dropKpa)+" kPa",14,false,WexspaceBrand.ICE));
            c.addView(text("Re  "+String.format(Locale.US,"%.0f",pri[i].reynolds)+"   f  "+String.format(Locale.US,"%.5f",pri[i].friction),11,false,WexspaceBrand.MUTED));
            double rel=Math.abs(ind[i].dropKpa-pri[i].dropKpa)/Math.max(Math.abs(pri[i].dropKpa),1e-12)*100.0;
            c.addView(text("Independent difference  "+String.format(Locale.US,"%.2f%%",rel),11,true,rel<=5?WexspaceBrand.GREEN:Color.RED));
            root.addView(c,margin(0,0,0,dp(10)));
        }
        double pHx101=source-pri[0].dropKpa-pri[1].dropKpa;
        double pHx102=source-pri[0].dropKpa-pri[2].dropKpa;
        LinearLayout end=card();end.setPadding(dp(16),dp(16),dp(16),dp(16));end.addView(text("ENDPOINT RESIDUAL PRESSURE",10,true,WexspaceBrand.CYAN));end.addView(text("HX-101  "+fmt(pHx101)+" kPa",18,true,WexspaceBrand.TEXT));end.addView(text("HX-102  "+fmt(pHx102)+" kPa",18,true,WexspaceBrand.TEXT));end.addView(text((pHx101>=150&&pHx102>=150)?"✓ Minimum residual pressure PASS":"Minimum pressure review required",12,true,(pHx101>=150&&pHx102>=150)?WexspaceBrand.GREEN:Color.RED));root.addView(end);
        return root;
    }
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
    private LinearLayout card(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setBackground(WexspaceBrand.panel(18,getResources().getDisplayMetrics().density));return l;}
    private TextView text(String s,int sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);if(bold)v.setTypeface(null,android.graphics.Typeface.BOLD);return v;}
    private LinearLayout.LayoutParams margin(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);p.setMargins(l,t,r,b);return p;}
}
