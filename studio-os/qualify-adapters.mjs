import fs from "node:fs";
import { execFileSync } from "node:child_process";
import * as THREE from "three";
import { animate } from "motion";
import { chromium } from "playwright";

const rows=[];
function pass(name,detail){rows.push({name,status:"PASS",detail:String(detail)});}
function fail(name,e){rows.push({name,status:"FAIL",detail:String(e?.message||e).slice(0,240)});}
function bin(name,args){
  return execFileSync(name,args,{encoding:"utf8",stdio:["ignore","pipe","pipe"]}).split("\n")[0].trim();
}

pass("node",process.version);
pass("three",THREE.REVISION);
pass("motion",typeof animate);
pass("playwright",typeof chromium.launch);

try { pass("lottie-web", import.meta.resolve("lottie-web")); } catch(e) { fail("lottie-web",e); }

for (const [name,args] of [["ffmpeg",["-version"]],["ffprobe",["-version"]],["Xvfb",["-help"]]]) {
  try { pass(name,bin(name,args)); } catch(e) { fail(name,e); }
}

try {
  const path=execFileSync("bash",["-lc","command -v xdotool"],{encoding:"utf8"}).trim();
  if(!path) throw new Error("xdotool not found");
  pass("xdotool",path);
} catch(e) { fail("xdotool",e); }

const ok=rows.every(x=>x.status==="PASS");
const receipt={
  schema:1,
  component:"WEXSPACE Studio OS Adapter Qualification",
  timestamp:new Date().toISOString(),
  rows,
  pass:ok
};
fs.writeFileSync("STUDIO_OS_ADAPTER_QUALIFICATION_R01.json",JSON.stringify(receipt,null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(!ok) process.exit(1);
