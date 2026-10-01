package ai.wexspace.fielddesk;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;

public final class RemoteLinkActivity extends Activity {
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(build());}
    private ScrollView build(){
        ScrollView s=new ScrollView(this);s.setBackgroundColor(WexspaceBrand.BG);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(24),dp(20),dp(42));s.addView(root);
        root.addView(text("←  PROJECT 03 / TELECOM + POWER",11,true,WexspaceBrand.CYAN));
        root.addView(text("Remote Link\nRescue Mission",31,true,WexspaceBrand.TEXT));
        TextView intro=text("A deterministic staged incident: preserve evidence, protect critical load, route two specialists, require human approval.",13,false,WexspaceBrand.MUTED);intro.setPadding(0,dp(10),0,dp(18));root.addView(intro);

        ProjectMath.RescueResult r=ProjectMath.rescue(2.4,0.40,0.20,120,600,5.5);
        LinearLayout incident=card();incident.addView(tag("INCIDENT FROZEN / EVIDENCE PRESERVED"));incident.addView(text("Relay battery at 40% SOC",19,true,Color.rgb(255,208,102)));incident.addView(text("Critical service load 120 W · reserve floor 20%",12,false,WexspaceBrand.MUTED));root.addView(incident,margin(dp(14)));

        LinearLayout metrics=new LinearLayout(this);metrics.setOrientation(LinearLayout.HORIZONTAL);
        metrics.addView(metric("USABLE",fmt(r.availableKwh)+" kWh"),weight());metrics.addView(metric("BATTERY",fmt(r.hoursBeforeReserve)+" h"),weight());metrics.addView(metric("PV RECOVERY",fmt(r.solarRecoveryW)+" W"),weight());
        root.addView(metrics,margin(dp(12)));

        LinearLayout route=card();route.addView(tag("SPECIALIST FLEET"));route.addView(text("Telecom Specialist  →  preserve link budget",14,true,WexspaceBrand.ICE));route.addView(text("Power Specialist    →  shed non-critical loads",14,true,WexspaceBrand.ICE));route.addView(text("Human Authority     →  approve recovery plan",14,true,WexspaceBrand.TEXT));root.addView(route,margin(dp(12)));

        LinearLayout verify=card();verify.addView(tag("RECOVERY RECEIPT"));verify.addView(text(r.overnightPass?"✓ OVERNIGHT SERVICE WINDOW RESTORED":"ESCALATE / ADD CAPACITY",17,true,r.overnightPass?WexspaceBrand.GREEN:Color.RED));verify.addView(text("EVIDENCE  LINK-RESCUE-001  •  HUMAN-APPROVED",11,true,WexspaceBrand.CYAN));verify.addView(text("Signal restored. Coffee subsystem still pending.",12,false,Color.rgb(255,208,102)));root.addView(verify);
        return s;
    }
    private LinearLayout metric(String a,String b){LinearLayout c=card();c.addView(text(a,9,true,WexspaceBrand.CYAN));c.addView(text(b,14,true,WexspaceBrand.TEXT));return c;}
    private TextView tag(String s){TextView v=text(s,10,true,WexspaceBrand.CYAN);v.setPadding(0,0,0,dp(8));return v;}
    private LinearLayout card(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(15),dp(14),dp(15),dp(14));l.setBackground(WexspaceBrand.panel(18,getResources().getDisplayMetrics().density));return l;}
    private TextView text(String s,int sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);if(bold)v.setTypeface(null,android.graphics.Typeface.BOLD);return v;}
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
    private LinearLayout.LayoutParams margin(int bottom){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);p.setMargins(0,0,0,bottom);return p;}
    private LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f);p.setMargins(dp(3),0,dp(3),0);return p;}
}
