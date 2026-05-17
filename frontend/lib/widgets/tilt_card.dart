import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class TiltCard extends StatefulWidget {
  final Widget child;
  final double tiltLimit;
  final double scale;
  final double perspective;
  final bool showSpotlight;

  const TiltCard({
    Key? key,
    required this.child,
    this.tiltLimit = 0.15,
    this.scale = 1.02,
    this.perspective = 0.001,
    this.showSpotlight = true,
  }) : super(key: key);

  @override
  State<TiltCard> createState() => _TiltCardState();
}

class _TiltCardState extends State<TiltCard> {
  double _rotateX = 0.0;
  double _rotateY = 0.0;
  Offset _spotlightPosition = const Offset(0.5, 0.5);
  bool _isHovered = false;

  void _onHover(PointerEvent event, Size size) {
    double px = event.localPosition.dx / size.width;
    double py = event.localPosition.dy / size.height;
    setState(() {
      _isHovered = true;
      _rotateX = (0.5 - py) * widget.tiltLimit;
      _rotateY = (px - 0.5) * widget.tiltLimit;
      _spotlightPosition = Offset(px, py);
    });
  }

  void _onExit(PointerExitEvent event) {
    setState(() {
      _isHovered = false;
      _rotateX = 0.0;
      _rotateY = 0.0;
    });
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final size = Size(constraints.maxWidth, constraints.maxHeight);
        final transform = Matrix4.identity()
          ..setEntry(3, 2, widget.perspective)
          ..rotateX(_rotateX)
          ..rotateY(_rotateY)
          ..scale(_isHovered ? widget.scale : 1.0);

        return MouseRegion(
          onHover: (event) => _onHover(event, size),
          onExit: _onExit,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
            transform: transform,
            transformAlignment: Alignment.center,
            child: Stack(
              clipBehavior: Clip.antiAlias,
              children: [
                widget.child,
                if (widget.showSpotlight)
                  AnimatedOpacity(
                    opacity: _isHovered ? 1.0 : 0.0,
                    duration: const Duration(milliseconds: 300),
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: RadialGradient(
                          center: FractionalOffset(
                              _spotlightPosition.dx, _spotlightPosition.dy),
                          radius: 1.0,
                          colors: [
                            Colors.white.withOpacity(0.1),
                            Colors.transparent
                          ],
                          stops: const [0.0, 0.5],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
