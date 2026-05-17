import 'dart:math';
import 'package:flutter/material.dart';
import '../core/constants.dart';

class ScoreGauge extends StatefulWidget {
  final int score;
  final String riskLevel;
  final double size;

  const ScoreGauge({
    super.key,
    required this.score,
    this.riskLevel = 'info',
    this.size = 200,
  });

  @override
  State<ScoreGauge> createState() => _ScoreGaugeState();
}

class _ScoreGaugeState extends State<ScoreGauge>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;
  late int _displayScore;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _animation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCubic,
    );
    _displayScore = 0;

    _animationController.addListener(() {
      setState(() {
        _displayScore = (widget.score * _animation.value).round();
      });
    });

    _animationController.forward();
  }

  @override
  void didUpdateWidget(ScoreGauge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.score != widget.score) {
      _animationController.reset();
      _animationController.forward();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Color _getScoreColor(int score) {
    if (score >= 80) return const Color(AppConstants.severityLow);
    if (score >= 50) return const Color(AppConstants.severityMedium);
    if (score >= 25) return const Color(AppConstants.severityHigh);
    return const Color(AppConstants.severityCritical);
  }

  @override
  Widget build(BuildContext context) {
    final scoreColor = _getScoreColor(widget.score);
    final bgColor = const Color(AppConstants.borderSubtle);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: widget.size,
          height: widget.size,
          child: CustomPaint(
            painter: _GaugePainter(
              score: widget.score.toDouble(),
              scoreColor: scoreColor,
              bgColor: bgColor,
              animationValue: _animation.value,
            ),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$_displayScore',
                    style: TextStyle(
                      fontSize: widget.size * 0.25,
                      fontWeight: FontWeight.bold,
                      color: scoreColor,
                    ),
                  ),
                  Text(
                    '/ 100',
                    style: TextStyle(
                      fontSize: widget.size * 0.08,
                      color: const Color(AppConstants.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Container(
          width: widget.size * 0.8,
          height: 4,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(2),
            color: bgColor,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: Row(
              children: [
                Expanded(
                    flex: 20,
                    child: Container(
                        color: const Color(AppConstants.riskCritical))),
                Expanded(
                    flex: 20,
                    child:
                        Container(color: const Color(AppConstants.riskHigh))),
                Expanded(
                    flex: 20,
                    child:
                        Container(color: const Color(AppConstants.riskMedium))),
                Expanded(
                    flex: 20,
                    child: Container(color: const Color(AppConstants.riskLow))),
                Expanded(
                    flex: 20,
                    child:
                        Container(color: const Color(AppConstants.riskInfo))),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        SizedBox(
          width: widget.size * 0.8,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('0',
                  style: TextStyle(
                      fontSize: 9, color: Color(AppConstants.textDisabled))),
              const Text('100',
                  style: TextStyle(
                      fontSize: 9, color: Color(AppConstants.textDisabled))),
            ],
          ),
        ),
      ],
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double score;
  final Color scoreColor;
  final Color bgColor;
  final double animationValue;

  _GaugePainter({
    required this.score,
    required this.scoreColor,
    required this.bgColor,
    required this.animationValue,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 12;
    final rect = Rect.fromCircle(center: center, radius: radius);

    final bgPaint = Paint()
      ..color = bgColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(rect, -pi / 2, 2 * pi, false, bgPaint);

    final animatedScore = score * animationValue;
    final sweepAngle = (animatedScore / 100) * 2 * pi;

    if (sweepAngle > 0) {
      final gradient = SweepGradient(
        startAngle: -pi / 2,
        endAngle: -pi / 2 + sweepAngle,
        colors: [
          scoreColor.withOpacity(0.6),
          scoreColor,
        ],
      );

      final gradientPaint = Paint()
        ..shader = gradient.createShader(rect)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 14
        ..strokeCap = StrokeCap.round;

      canvas.drawArc(rect, -pi / 2, sweepAngle, false, gradientPaint);
    }

    if (animatedScore > 0) {
      final dotAngle = -pi / 2 + sweepAngle;
      final dotX = center.dx + radius * cos(dotAngle);
      final dotY = center.dy + radius * sin(dotAngle);

      canvas.drawCircle(
        Offset(dotX, dotY),
        8,
        Paint()..color = scoreColor,
      );
      canvas.drawCircle(
        Offset(dotX, dotY),
        4,
        Paint()..color = Colors.white,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _GaugePainter oldDelegate) {
    return oldDelegate.score != score ||
        oldDelegate.animationValue != animationValue;
  }
}
