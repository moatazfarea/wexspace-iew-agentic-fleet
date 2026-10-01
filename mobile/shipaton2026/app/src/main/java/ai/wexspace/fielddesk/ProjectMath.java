package ai.wexspace.fielddesk;

public final class ProjectMath {
    private ProjectMath() {}

    public static final class PumpResult {
        public final double velocity, reynolds, friction, losses, tdh, shaftKw;
        public final boolean verificationPass;
        PumpResult(double velocity,double reynolds,double friction,double losses,double tdh,double shaftKw,boolean verificationPass){
            this.velocity=velocity;this.reynolds=reynolds;this.friction=friction;this.losses=losses;this.tdh=tdh;this.shaftKw=shaftKw;this.verificationPass=verificationPass;
        }
    }

    public static PumpResult pump(double flowM3h,double diameterM,double lengthM,double staticM,double minorK,double efficiency){
        double rho=997.0, mu=0.00089, g=9.80665;
        double q=flowM3h/3600.0, area=Math.PI*diameterM*diameterM/4.0, v=q/area;
        double re=rho*v*diameterM/mu;
        double f=0.25/Math.pow(Math.log10(0.000045/(3.7*diameterM)+5.74/Math.pow(re,0.9)),2);
        double major=f*(lengthM/diameterM)*(v*v/(2*g));
        double minor=minorK*(v*v/(2*g));
        double tdh=staticM+major+minor;
        double kw=rho*g*q*tdh/(Math.max(efficiency,0.01)*1000.0);

        double fh=1.0/Math.pow(-1.8*Math.log10(Math.pow(0.000045/(3.7*diameterM),1.11)+6.9/re),2);
        double tdh2=staticM+(fh*(lengthM/diameterM)+minorK)*(v*v/(2*g));
        boolean pass=Math.abs(tdh2-tdh)/Math.max(tdh,1e-9)<=0.05;
        return new PumpResult(v,re,f,major+minor,tdh,kw,pass);
    }

    public static final class SolarResult {
        public final double pvKw,batteryKwh,inverterKw,annualKwh;
        public final boolean pass;
        SolarResult(double pvKw,double batteryKwh,double inverterKw,double annualKwh,boolean pass){
            this.pvKw=pvKw;this.batteryKwh=batteryKwh;this.inverterKw=inverterKw;this.annualKwh=annualKwh;this.pass=pass;
        }
    }

    public static SolarResult solar(double dailyKwh,double peakKw,double psh,double derate,double autonomy,double dod,double roundTrip){
        double pv=dailyKwh/(psh*derate);
        double battery=dailyKwh*autonomy/(dod*roundTrip);
        double inverter=Math.max(peakKw*1.25,1.0);
        double annual=pv*psh*365.0*derate;
        boolean pass=pv*psh*derate>=dailyKwh && battery*dod*roundTrip>=dailyKwh*autonomy;
        return new SolarResult(pv,battery,inverter,annual,pass);
    }

    public static final class RescueResult {
        public final double availableKwh,hoursBeforeReserve,solarRecoveryW,criticalLoadW;
        public final boolean overnightPass;
        RescueResult(double availableKwh,double hoursBeforeReserve,double solarRecoveryW,double criticalLoadW,boolean overnightPass){
            this.availableKwh=availableKwh;this.hoursBeforeReserve=hoursBeforeReserve;this.solarRecoveryW=solarRecoveryW;this.criticalLoadW=criticalLoadW;this.overnightPass=overnightPass;
        }
    }

    public static RescueResult rescue(double batteryKwh,double soc,double reserve,double criticalW,double solarW,double sunHours){
        double available=batteryKwh*Math.max(0,soc-reserve);
        double hours=available/(criticalW/1000.0);
        double solarRecovery=solarW*sunHours/1000.0;
        boolean pass=hours>=4.0 || (available+solarRecovery)/(criticalW/1000.0)>=10.0;
        return new RescueResult(available,hours,solarW,criticalW,pass);
    }
}
