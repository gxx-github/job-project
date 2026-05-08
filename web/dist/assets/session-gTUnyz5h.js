import{s as u,x as w,r as c}from"./index-CZJY0s-L.js";/**
 * @license lucide-vue-next v0.503.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h=e=>e.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),m=e=>e.replace(/^([A-Z])|[\s-_]+(\w)/g,(t,s,o)=>o?o.toUpperCase():s.toLowerCase()),v=e=>{const t=m(e);return t.charAt(0).toUpperCase()+t.slice(1)},C=(...e)=>e.filter((t,s,o)=>!!t&&t.trim()!==""&&o.indexOf(t)===s).join(" ").trim();/**
 * @license lucide-vue-next v0.503.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var i={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-vue-next v0.503.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g=({size:e,strokeWidth:t=2,absoluteStrokeWidth:s,color:o,iconNode:l,name:a,class:d,...n},{slots:r})=>u("svg",{...i,width:e||i.width,height:e||i.height,stroke:o||i.stroke,"stroke-width":s?Number(t)*24/Number(e):t,class:C("lucide",...a?[`lucide-${h(v(a))}-icon`,`lucide-${h(a)}`]:["lucide-icon"]),...n},[...l.map(f=>u(...f)),...r.default?[r.default()]:[]]);/**
 * @license lucide-vue-next v0.503.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b=(e,t)=>(s,{slots:o})=>u(g,{...s,iconNode:t,name:e},o),k=w("session",()=>{const e=c(""),t=c(""),s=c(""),o=c("");function l(n,r){e.value=n,t.value=r}function a(n,r){s.value=n,o.value=r}function d(){e.value="",t.value="",s.value="",o.value=""}return{sessionId:e,fileName:t,jobName:s,jobAge:o,setSession:l,setJobParams:a,reset:d}});export{b as c,k as u};
