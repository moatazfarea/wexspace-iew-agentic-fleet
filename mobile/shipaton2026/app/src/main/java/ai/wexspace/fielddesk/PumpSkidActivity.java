package ai.wexspace.fielddesk;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;

public final class PumpSkidActivity extends Activity {
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(build());}
    private ScrollView build(){
        ScrollView s=new ScrollView(this);s.setBackgroundColor(WexspaceBrand.BG);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(24),dp(20),dp(42));s.addView(root);
        root.addView(text("←  PROJECT 01 / MECHANICAL",11,true,WexspaceBrand.CYAN));
        root.addView(text("Compact Pump Skid\nDuty-Point Design",31,true,WexspaceBrand.TEXT));
        TextView intro=text("Human request → hydraulic specialist → deterministic solver → independent friction cross-check → evidence receipt.",13,false,WexspaceBrand.MUTED);intro.setPadding(0,dp(10),0,dp(18));root.addView(intro);

        ProjectMath.PumpResult r=ProjectMath.pump(18.0,0.065,85.0,24.0,6.0,0.68);
        LinearLayout req=card();req.addView(tag("APPROVED INPUT"));req.addView(text("18 m³/h   •   24 m static lift   •   85 m run",18,true,WexspaceBrand.TEXT));req.addView(text("Water · Ø65 mm · minor-loss K=6 · pump η=68%",12,false,WexspaceBrand.MUTED));root.addView(req,margin(dp(14)));

        LinearLayout metrics=new LinearLayout(this);metrics.setOrientation(LinearLayout.HORIZONTAL);
        metrics.addView(metric("TDH",fmt(r.tdh)+" m"),weight());metrics.addView(metric("VELOCITY",fmt(r.velocity)+" m/s"),weight());metrics.addView(metric("SHAFT",fmt(r.shaftKw)+" kW"),weight());
        root.addView(metrics,margin(dp(12)));

        LinearLayout calc=card();calc.addView(tag("DETERMINISTIC TRACE"));calc.addView(text("Reynolds   "+String.format(Locale.US,"%.0f",r.reynolds),14,true,WexspaceBrand.ICE));calc.addView(text("Swamee–Jain f   "+String.format(Locale.US,"%.4f",r.friction),13,false,WexspaceBrand.MUTED));calc.addView(text("Pipe + minor losses   "+fmt(r.losses)+" m",13,false,WexspaceBrand.MUTED));calc.addView(text("Selected motor   4.0 kW",16,true,WexspaceBrand.TEXT));root.addView(calc,margin(dp(12)));

        LinearLayout verify=card();verify.addView(tag("INDEPENDENT VERIFIER"));verify.addView(text(r.verificationPass?"✓ HAALAND CROSS-CHECK PASS":"REVIEW REQUIRED",17,true,r.verificationPass?WexspaceBrand.GREEN:Color.RED));verify.addView(text("Result tolerance ≤ 5% · no simulated PASS",12,false,WexspaceBrand.MUTED));verify.addView(text("EVIDENCE  PUMP-SKID-001  •  HASH-BOUND",11,true,WexspaceBrand.CYAN));root.addView(verify);
        return s;
    }
    private LinearLayout metric(String a,String b){LinearLayout c=card();c.addView(text(a,9,true,WexspaceBrand.CYAN));c.addView(text(b,15,true,WexspaceBrand.TEXT));return c;}
    private TextView tag(String s){TextView v=text(s,10,true,WexspaceBrand.CYAN);v.setPadding(0,0,0,dp(8));return v;}
    private LinearLayout card(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(15),dp(14),dp(15),dp(14));l.setBackground(WexspaceBrand.panel(18,getResources().getDisplayMetrics().density));return l;}
    private TextView text(String s,int sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);if(bold)v.setTypeface(null,android.graphics.Typeface.BOLD);return v;}
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
    private LinearLayout.LayoutParams margin(int bottom){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);p.setMargins(0,0,0,bottom);return p;}
    private LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f);p.setMargins(dp(3),0,dp(3),0);return p;}
}
