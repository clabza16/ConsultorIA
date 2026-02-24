document.addEventListener('DOMContentLoaded', () => {
    const salaryInput = document.getElementById('salary');
    const taskInputs = document.querySelectorAll('.task-hours');
    const monthlySavingsText = document.getElementById('monthly-savings');
    const annualSavingsText = document.getElementById('annual-savings');
    const hoursSavedText = document.getElementById('hours-saved');

    const calculateROI = () => {
        const salary = parseFloat(salaryInput.value) || 0;
        let totalWeeklyHours = 0;

        taskInputs.forEach(input => {
            totalWeeklyHours += parseFloat(input.value) || 0;
        });

        // Assumptions:
        // 1. A typical professional works ~160 hours per month.
        // IA reduces these specific tasks by 20% (Updated per user request).
        const hourlyRate = salary / 160;
        const weeklySavingsInHours = totalWeeklyHours * 0.2; // 20% efficiency gain
        const monthlySavingsInHours = weeklySavingsInHours * 4.33;
        const monthlyMoneySaved = monthlySavingsInHours * hourlyRate;
        const annualMoneySaved = monthlyMoneySaved * 12;

        // Formatter for CLP (Chilean Peso) or generic currency
        const formatter = new Intl.NumberFormat('es-CL', {
            style: 'currency',
            currency: 'CLP',
            minimumFractionDigits: 0
        });

        monthlySavingsText.innerText = formatter.format(monthlyMoneySaved);
        annualSavingsText.innerText = formatter.format(annualMoneySaved);
        hoursSavedText.innerText = `${Math.round(monthlySavingsInHours)} horas`;
    };

    salaryInput.addEventListener('input', calculateROI);
    taskInputs.forEach(input => {
        input.addEventListener('input', calculateROI);
    });

    // Initial calculation
    calculateROI();
});
