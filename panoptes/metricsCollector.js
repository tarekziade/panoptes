"use strict";

async function getMetrics() {
    let results = {};
    results['performance'] = await ChromeUtils.requestPerformanceMetrics();
    results['io'] = await ChromeUtils.requestIOActivity();
    // make procinfo a promise..
    results['proc'] = ChromeUtils.getProcInfo();
    return results;
}

return getMetrics();
