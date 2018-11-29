"use strict";

ChromeUtils.import("resource://gre/modules/Troubleshoot.jsm");

async function getSupport() {
  var data = await new Promise((resolve, reject) => {
    Troubleshoot.snapshot((data) => {
      resolve(data);
    });
  });
  return data;
}

return getSupport();
