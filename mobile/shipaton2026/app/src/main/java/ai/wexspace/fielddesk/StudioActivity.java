package ai.wexspace.fielddesk;

import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class StudioActivity extends Activity {
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(build());}
    private LinearLayout build(){
        ScrollView s=new ScrollView(this);s.setBackgroundColor(WexspaceBrand.BG);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(24),dp(20),dp(38));s.addView(root);
        root.addView(text("←  STUDIO OS / PRODUCTION JOB #001",11,true,WexspaceBrand.CYAN));
        root.addView(text("Cinematic Execution\nControl Plane",30,true,WexspaceBrand.TEXT));
        TextView d=text("Brand-consistent scene orchestration, high-frame-rate capture, evidence synchronization and deterministic render QA.",13,false,WexspaceBrand.MUTED);d.setPadding(0,dp(10),0,dp(18));root.addView(d);
        String[][] beats={
            {"00:00–00:07","ORBITAL COLD OPEN","Brand reveal · 3 project lanes · no dead time"},
            {"00:07–00:30","THREE PROJECTS","Engineering → Software/QA → Studio OS"},
            {"00:30–00:55","EXECUTION DEPTH","Tools · agents · evidence · smooth camera"},
            {"00:55–01:12","CONTINUITY","Preserved state · no duplicate execution"},
            {"01:12–01:34","WEXSPACE PRO","RevenueCat offering → entitlement → capability"},
            {"01:34–01:49","HUMAN AUTHORITY","Configured ≠ Authorized ≠ Executed ≠ Verified"},
            {"01:49–01:55","NEXT GEN CLOSE","Open source · Android · WEXSPACE"}
        };
        for(String[] b:beats){
            LinearLayout c=card();c.setPadding(dp(16),dp(14),dp(16),dp(14));c.addView(text(b[0],10,true,WexspaceBrand.CYAN));c.addView(text(b[1],17,true,WexspaceBrand.TEXT));c.addView(text(b[2],12,false,WexspaceBrand.MUTED));root.addView(c,margin(0,0,0,dp(9)));
        }
        LinearLayout stack=card();stack.setPadding(dp(16),dp(16),dp(16),dp(16));stack.addView(text("CAPTURE / RENDER ADAPTERS",10,true,WexspaceBrand.CYAN));stack.addView(text("Playwright · Chromium · Xvfb · FFmpeg 60fps · Three.js · Motion · Android Emulator",13,true,WexspaceBrand.ICE));stack.addView(text("Truth classes: LIVE · REPLAY · STAGED_DETERMINISTIC. Never simulated success.",11,false,WexspaceBrand.MUTED));root.addView(stack);
        return root;
    }
    private LinearLayout card(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setBackground(WexspaceBrand.panel(18,getResources().getDisplayMetrics().density));return l;}
    private TextView text(String s,int sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);if(bold)v.setTypeface(null,android.graphics.Typeface.BOLD);return v;}
    private LinearLayout.LayoutParams margin(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);p.setMargins(l,t,r,b);return p;}
}
