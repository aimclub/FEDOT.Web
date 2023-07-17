"use strict";(self.webpackChunkfedot=self.webpackChunkfedot||[]).push([[828],{24433:function(r,n,e){var t=e(61974),o=e(76914),i=(0,t.ZP)(o.Z)({minHeight:48,fontFamily:"'Open sans'",fontStyle:"normal",fontWeight:400,fontSize:16,lineHeight:"120%",textAlign:"center",textTransform:"none",borderRadius:"4px",background:"#263238",color:"#ffffff","&:disabled":{background:"#ECEFF1"},"&:hover":{background:"#515B5F"}});n.Z=i},15368:function(r,n,e){e.d(n,{Z:function(){return u}});var t="mFqXDJcs",o=e(25439),i=e(85246),a=e(85893),u=function(r){var n=r.hasBlackout,e=void 0!==n&&n,u=r.className;return(0,a.jsx)("div",{className:(0,i.cl)(e&&t,u),children:(0,a.jsx)(o.VF,{color:"#94CE45",secondaryColor:"#263238",height:100,width:100})})}},97748:function(r,n,e){var t=e(79542),o=e(61974),i=e(67294),a=e(85893),u=(0,o.ZP)(t.Z)({margin:"0 0 14px 0",color:"#000","& .MuiOutlinedInput-notchedOutline":{border:"1px solid #B0BEC5"},".MuiInputBase-root":{"&.Mui-focused .MuiOutlinedInput-notchedOutline":{border:"1px solid #78909C"},"&:hover:not(.Mui-disabled):not(.Mui-focused) .MuiOutlinedInput-notchedOutline":{border:"1px solid #90A4AE"},"&.Mui-disabled .MuiOutlinedInput-notchedOutline":{border:"1px solid #ECEFF1"}},"& .MuiInputLabel-root":{fontFamily:"'Open sans'",fontStyle:"normal",fontWeight:400,fontSize:16,lineHeight:"120%",textTransform:"capitalize"},"& .MuiInputLabel-root:not(.Mui-error)":{color:"#B0BEC5"},"& .MuiInputLabel-root.Mui-focused:not(.Mui-error)":{color:"#78909C"},"& .MuiInputLabel-root.Mui-disabled":{color:"#ECEFF1"},"& .MuiOutlinedInput-input":{padding:"15px 22px",fontFamily:"'Open sans'",fontStyle:"normal",fontWeight:400,fontSize:16,lineHeight:"120%"},"& .MuiInputLabel-root:not(.MuiInputLabel-shrink)":{transform:"translate(22px, 15px)"},"& .Mui-disabled.MuiOutlinedInput-input":{color:"#ECEFF1"},"& .MuiFormHelperText-root":{margin:"4px 0 0 22px",fontFamily:"'Open sans'",fontStyle:"normal",fontWeight:400,fontSize:12,lineHeight:"120%"}}),s=function(r){var n=r.name,e=r.label,t=r.type,o=r.value,i=r.onChange,s=r.disabled,l=r.className,c=r.error;return(0,a.jsx)(u,{variant:"outlined",className:l,label:e||n,name:n,type:t,value:o,onChange:i,disabled:s,error:!!c,helperText:c||""})};n.Z=(0,i.memo)(s)},85809:function(r,n,e){e.d(n,{B:function(){return s},p:function(){return u}});var t=e(16310),o=e(64682),i=t.Z_().min(2,(function(r){var n=r.min;return o.N.min(n)})).max(15,(function(r){var n=r.max;return o.N.max(n)})).required(o.N.required),a=t.Z_().required(o.N.required),u=t.Ry().shape({email:i,password:a}),s=t.Ry().shape({email:i,password:a,confirm_password:a.oneOf([t.iH("password")],o.N.repeat("Passwords"))})},9828:function(r,n,e){e.r(n),e.d(n,{default:function(){return y}});var t=e(66626),o=e(76914),i=e(67294),a=e(79655),u=e(21848),s=e(15368),l=e(9890),c=e(41054),d=e(97748),f=e(24433),m=e(85809),p=e(85893),h=function(r){var n=r.signUp,e=r.isError,t=(0,c.TA)({initialValues:{email:"",password:"",confirm_password:""},validationSchema:m.B,onSubmit:function(r){return n({email:r.email,password:r.password})}}),o=t.handleSubmit,i=t.handleChange,a=t.values,u=t.errors,s=t.touched;return(0,p.jsxs)("form",{onSubmit:o,className:l.Z.root,children:[(0,p.jsx)(d.Z,{name:"email",label:"login *",value:a.email,onChange:i,error:s.email?u.email:void 0}),(0,p.jsx)(d.Z,{name:"password",label:"password *",type:"password",value:a.password,onChange:i,error:s.password?u.password:void 0}),(0,p.jsx)(d.Z,{name:"confirm_password",label:"password *",type:"password",value:a.confirm_password,onChange:i,error:s.confirm_password?u.confirm_password:void 0}),(0,p.jsx)("div",{className:l.Z.error,children:e&&(0,p.jsx)("p",{children:"Authorization error!"})}),(0,p.jsx)(f.Z,{type:"submit",children:(0,p.jsx)("span",{children:"Register"})})]})},b=(0,i.memo)(h),g=e(41628);function x(r,n){return function(r){if(Array.isArray(r))return r}(r)||function(r,n){var e=null==r?null:"undefined"!=typeof Symbol&&r[Symbol.iterator]||r["@@iterator"];if(null!=e){var t,o,i,a,u=[],s=!0,l=!1;try{if(i=(e=e.call(r)).next,0===n){if(Object(e)!==e)return;s=!1}else for(;!(s=(t=i.call(e)).done)&&(u.push(t.value),u.length!==n);s=!0);}catch(r){l=!0,o=r}finally{try{if(!s&&null!=e.return&&(a=e.return(),Object(a)!==a))return}finally{if(l)throw o}}return u}}(r,n)||function(r,n){if(!r)return;if("string"==typeof r)return v(r,n);var e=Object.prototype.toString.call(r).slice(8,-1);"Object"===e&&r.constructor&&(e=r.constructor.name);if("Map"===e||"Set"===e)return Array.from(r);if("Arguments"===e||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(e))return v(r,n)}(r,n)||function(){throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}function v(r,n){(null==n||n>r.length)&&(n=r.length);for(var e=0,t=new Array(n);e<n;e++)t[e]=r[e];return t}var y=function(){var r=x(u.k.useSigninMutation(),2),n=r[0],e=r[1],l=e.isLoading,c=e.isError,d=x(u.k.useRegisterMutation(),2),f=d[0],m=d[1],h=m.isLoading,v=m.isError,y=(0,i.useCallback)((function(){n({email:"guest",password:"guest"})}),[n]);return(0,p.jsxs)(p.Fragment,{children:[(h||l)&&(0,p.jsx)(s.Z,{hasBlackout:!0}),(0,p.jsx)("h1",{className:t.Z.title,children:"Registration"}),(0,p.jsx)(b,{signUp:f,isError:v||c}),(0,p.jsxs)("div",{className:t.Z.foot,children:[(0,p.jsx)(a.rU,{to:g.TD.SIGNIN,className:t.Z.footItem,children:"Already registered? Sign In"}),(0,p.jsx)(o.Z,{onClick:y,className:t.Z.footItem,children:"Sign In as guest"})]})]})}},85246:function(r,n,e){e.d(n,{cl:function(){return t}});var t=function(){for(var r=arguments.length,n=new Array(r),e=0;e<r;e++)n[e]=arguments[e];return n.map((function(r){return r||void 0})).join(" ")}},64682:function(r,n,e){e.d(n,{N:function(){return t}});var t={required:"Required!",min:function(r){return"Mininum ".concat(r," characters!")},max:function(r){return"Maximum ".concat(r," characters!")},repeat:function(r){return"".concat(r," not match!")},unique:function(r){return"".concat(r," already exists!")}}},9890:function(r,n){n.Z={root:"T7S4hwzO",error:"xk9G_mQw"}},66626:function(r,n){n.Z={root:"O18IGSxE",logo:"TSccxkbc",paper:"GbEyCPI8",loader:"IQovLHPm",title:"DrFSabpF",foot:"jCESkU4u",footItem:"_nqIY3rs"}}}]);
//# sourceMappingURL=828.chunk.js.map