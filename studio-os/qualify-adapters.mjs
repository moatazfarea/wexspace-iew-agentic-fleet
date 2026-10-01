import fs from "node:fs";
import { execFileSync } from "node:child_process";
import * as THREE from "three";
import { animate } from "motion";
import { chromium } from "playwright";
import lottie from "lottie-web";

const rows=[];
function ok(name,detail){rows.push({name,status:"PASS",detail});}
function bin(name,args=["-version"]){const out=execFileSync(name,args,{encoding:"utf8",stdio:["ignore","pipe","pipe"]});return out.split("\n")[0].trim();}
ok("node",process.version);
ok("three",THREE.REVISION);
ok("motion",typeof animate);
ok("lottie-web",typeof lottie.loadAnimation);
ok("playwright",typeof chromium.launch);
for(const [name,args] of [["ffmpeg",["-version"]],["ffprobe",["-version"]],["Xvfb",["-help"]],["xdotool",["help"]]]){
  try{ok(name,bin(name,args));}catch(e){rows.push({name,status:"FAIL",detail:String(e.message).slice(0,220)});}
}
const pass=rows.every(x=>x.status==="PASS");
const receipt={schema:1,component:"WEXSPACE Studio OS Adapter Qualification",timestamp:new Date().toISOString(),rows,pass};
fs.writeFileSync("STUDIO_OS_ADAPTER_QUALIFICATION_R01.json",JSON.stringify(receipt,null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(!pass)process.exit(1);
