const fs = require('fs');
const p = __dirname + '/app/(protected)/logging-configuration/page.tsx';
let c = fs.readFileSync(p, 'utf8');

// Fix line: const { isAuthenticated } = useAuth() - should have 2 leading spaces
c = c.replace(/(?:^|\n)(\s*)const \{ isAuthenticated \} = useAuth\(\)/, '\n  const { isAuthenticated } = useAuth()');

// Fix fetchConfig try-catch indentation
c = c.replace(/(?:^|\n)(\s*)const fetchConfig = async \(\) => \{\n\s*try \{/, '\n  const fetchConfig = async () => {\n    try {');

// Fix handleResetToDefaults indentation
c = c.replace(/(?:^|\n)(\s*)const handleResetToDefaults = \(\) => \{/, '\n  const handleResetToDefaults = () => {');

// Fix if (!isAuthenticated) indentation
c = c.replace(/(?:^|\n)(\s*)if \(!isAuthenticated\) \{/, '\n  if (!isAuthenticated) {');

// Fix return and form section indentation
c = c.replace(/(?:^|\n)(\s*)return \(/, '\n  return (');

fs.writeFileSync(p, c, 'utf8');
console.log('Fixed indentation');