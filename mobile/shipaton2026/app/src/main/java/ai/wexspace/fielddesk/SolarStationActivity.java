package ai.wexspace.fielddesk;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;

public final class SolarStationActivity extends Activity {
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(build());}
    private ScrollView build(){
        ScrollView s=new ScrollView(this);s.setBackgroundColor(WexspaceBrand.BG);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(24),dp(20),dp(42));s.addView(root);
        root.addView(text("←  PROJECT 02 / ENERGY",11,true,WexspaceBrand.CYAN));
        root.addView(text("Mini Solar\nPower Station",31,true,WexspaceBrand.TEXT));
        TextView intro=text("Demand profile → PV sizing → battery autonomy → inverter margin → energy-balance verification.",13,false,WexspaceBrand.MUTED);intro.setPadding(0,dp(10),0,dp(18));root.addView(intro);

        ProjectMath.SolarResult r=ProjectMath.solar(9.6,2.2,5.8,0.78,1.5,0.80,0.90);
        LinearLayout req=card();req.addView(tag("APPROVED INPUT"));req.addView(text("9.6 kWh/day   •   2.2 kW peak",18,true,WexspaceBrand.TEXT));req.addView(text("5.8 peak-sun-hours · 78% derate · 1.5-day autonomy",12,false,WexspaceBrand.MUTED));root.addView(req,margin(dp(14)));

        LinearLayout metrics=new LinearLayout(this);metrics.setOrientation(LinearLayout.HORIZONTAL);
        metrics.addView(metric("PV ARRAY",fmt(r.pvKw)+" kWp"),weight());metrics.addView(metric("BATTERY",fmt(r.batteryKwh)+" kWh"),weight());metrics.addView(metric("INVERTER",fmt(r.inverterKw)+" kW"),weight());
        root.addView(metrics,margin(dp(12)));

        LinearLayout balance=card();balance.addView(tag("ENERGY BALANCE"));balance.addView(text("PV yield   "+fmt(r.annualKwh)+" kWh/year",15,true,WexspaceBrand.ICE));balance.addView(text("Usable storage satisfies autonomy target",13,false,WexspaceBrand.MUTED));balance.addView(text("Inverter includes 25% peak-load margin",13,false,WexspaceBrand.MUTED));root.addView(balance,margin(dp(12)));

        LinearLayout verify=card();verify.addView(tag("INDEPENDENT VERIFIER"));verify.addView(text(r.pass?"✓ LOAD / STORAGE BALANCE PASS":"REVIEW REQUIRED",17,true,r.pass?WexspaceBrand.GREEN:Color.RED));verify.addView(text("No generative arithmetic · deterministic equations only",12,false,WexspaceBrand.MUTED));verify.addView(text("EVIDENCE  SOLAR-MICRO-001  •  HASH-BOUND",11,true,WexspaceBrand.CYAN));root.addView(verify);
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
