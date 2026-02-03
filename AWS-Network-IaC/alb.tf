# Application Load Balancer Configuration
# Author: Navaneethraj KA

# Application Load Balancer
resource "aws_lb" "main" {
  count = var.enable_alb ? 1 : 0

  name               = "${var.project_name}-alb"
  internal           = var.alb_internal
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-alb"
  })
}

# HTTP Listener (redirects to HTTPS)
resource "aws_lb_listener" "http" {
  count = var.enable_alb ? 1 : 0

  load_balancer_arn = aws_lb.main[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener (returns fixed response - needs certificate for actual use)
resource "aws_lb_listener" "https" {
  count = var.enable_alb ? 1 : 0

  load_balancer_arn = aws_lb.main[0].arn
  port              = 443
  protocol          = "HTTP" # Change to HTTPS when you have a certificate

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Ready to serve!"
      status_code  = "200"
    }
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  count = var.enable_alb ? 1 : 0

  name     = "${var.project_name}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200-299"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-tg"
  })
}

# Listener Rule for target group
resource "aws_lb_listener_rule" "app" {
  count = var.enable_alb ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app[0].arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
