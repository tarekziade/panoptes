"use strict";

async function getMetrics() {
    let results = {};
    results['performance'] = await ChromeUtils.requestPerformanceMetrics();
    results['io'] = await ChromeUtils.requestIOActivity();
    // XXX add process info
    return results;
}

return getMetrics();
